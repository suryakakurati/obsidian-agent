import numpy as np
from pathlib import Path

from faiss_index import (
    load_index, build_index, save_index,
    load_embeddings, faiss_search
)
from bm25 import load_bm25, bm25_search, build_bm25_index, _tokenize, BM25Okapi  # noqa: F401 — backward compat for old pickles
from llm import generate_embedding
from vector import normalize

RRF_K = 60
FAISS_FLOOR = 0.52
FAISS_GUARANTEE = 0.80
SUGGEST_TOP_K = 5
MIN_QUERY_TOKENS = 5


def _rrf_merge(faiss_results: list[dict], bm25_results: list[dict], top_k: int) -> list[dict]:
    scores = {}
    for rank, r in enumerate(faiss_results):
        scores[r["path"]] = scores.get(r["path"], 0) + 1 / (RRF_K + rank + 1)
    for rank, r in enumerate(bm25_results):
        scores[r["path"]] = scores.get(r["path"], 0) + 1 / (RRF_K + rank + 1)
    sorted_paths = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [{"path": p, "hybrid": scores[p]} for p in sorted_paths]


def filter_by_tiers(results: list[dict], top_k: int = SUGGEST_TOP_K) -> list[dict]:
    if top_k < 1:
        return []

    non_self = [r for r in results if r["faiss"] < 0.99]
    guaranteed = [r for r in non_self if r["faiss"] > FAISS_GUARANTEE]
    middle = [r for r in non_self if FAISS_FLOOR <= r["faiss"] <= FAISS_GUARANTEE]

    guaranteed.sort(key=lambda r: r["faiss"], reverse=True)
    middle.sort(key=lambda r: r["hybrid"], reverse=True)

    output = guaranteed[:top_k]
    if len(output) < top_k:
        output.extend(middle[:top_k - len(output)])

    return output


def build_and_persist_index():
    paths, vectors = load_embeddings()
    if len(paths) == 0:
        return
    index = build_index(vectors)
    save_index(index, paths)
    print(f"FAISS index persisted ({len(paths)} vectors)")
    try:
        build_bm25_index(paths)
        print(f"BM25 index persisted ({len(paths)} docs)")
    except Exception as e:
        print(f"Warning: Failed to persist BM25 index: {e}")


def search(query: str, k: int = 5):
    if k < 1:
        return []
    if not query or not query.strip():
        return []
    if len(_tokenize(query)) < MIN_QUERY_TOKENS:
        return []
    query_vec = generate_embedding(query)
    if not query_vec:
        return []
    query_vec = normalize(query_vec).astype("float32")
    query_vec = np.expand_dims(query_vec, axis=0)

    paths, index = load_index()
    if paths is None:
        paths, vectors = load_embeddings()
        if len(paths) == 0:
            return []
        index = build_index(vectors)

    faiss_results = faiss_search(query_vec, index, paths, k)

    bm25_paths, bm25 = load_bm25()
    bm25_results = bm25_search(query, bm25, bm25_paths, k)

    merged = _rrf_merge(faiss_results, bm25_results, k)

    faiss_lookup = {r["path"]: r["faiss_score"] for r in faiss_results}
    bm25_lookup = {r["path"]: r["bm25_score"] for r in bm25_results}

    results = []
    for r in merged:
        path = r["path"]
        results.append({
            "name": Path(path).stem,
            "path": path,
            "faiss": faiss_lookup.get(path, 0.0),
            "bm25": bm25_lookup.get(path, 0.0),
            "hybrid": r["hybrid"]
        })
    return results
