from pathlib import Path
from collections import Counter
import numpy as np
import pickle
import re

from config import DB_PATH

INDEX_DIR = Path(DB_PATH).parent
BM25_FILE = INDEX_DIR / "notes.bm25"

BM25_K1 = 1.5
BM25_B = 0.75
TITLE_BOOST = 3


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r'\w+', text.lower()) if len(t) >= 2]


class BM25Okapi:
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size if corpus else 0
        self.doc_freqs = [Counter(doc) for doc in corpus]
        self.doc_len = [len(doc) for doc in corpus]
        self.idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        df = Counter()
        for doc_freq in self.doc_freqs:
            for term in doc_freq:
                df[term] += 1
        return {
            term: float(np.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1))
            for term, freq in df.items()
        }

    def get_scores(self, query: list[str]) -> list[float]:
        scores = [0.0] * self.corpus_size
        for term in query:
            if term not in self.idf:
                continue
            idf = self.idf[term]
            for i in range(self.corpus_size):
                tf = self.doc_freqs[i].get(term, 0)
                if tf:
                    scores[i] += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl))
        return scores

    def search(self, query: list[str], top_k: int = 10) -> list[tuple[int, float]]:
        scores = self.get_scores(query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(idx, scores[idx]) for idx in top_indices if scores[idx] > 0]


def build_bm25_index(paths: list[str]):
    if not paths:
        return

    corpus = []
    for path in paths:
        try:
            content = Path(path).read_text(encoding="utf-8", errors="ignore")
            title = Path(path).stem
            title_tokens = _tokenize(title) * TITLE_BOOST
            content_tokens = _tokenize(content)
            corpus.append(title_tokens + content_tokens)
        except Exception:
            corpus.append([])

    bm25 = BM25Okapi(corpus, k1=BM25_K1, b=BM25_B)
    with open(BM25_FILE, "wb") as f:
        pickle.dump({"bm25": bm25, "paths": paths}, f)


def load_bm25():
    if not BM25_FILE.exists():
        return None, None
    try:
        with open(BM25_FILE, "rb") as f:
            data = pickle.load(f)
        return data["paths"], data["bm25"]
    except Exception:
        return None, None


def bm25_search(query: str, bm25, bm25_paths, k: int) -> list[dict]:
    if bm25 is None:
        return []
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    bm25_raw = bm25.search(query_tokens, k)
    results = []
    for idx, score in bm25_raw:
        if idx < len(bm25_paths):
            results.append({"path": bm25_paths[idx], "bm25_score": float(score)})
    return results
