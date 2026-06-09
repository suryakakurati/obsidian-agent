from pathlib import Path
import sqlite3
import numpy as np
import faiss
import json

from config import DB_PATH
from vector import from_blob

INDEX_DIR = Path(DB_PATH).parent
INDEX_FILE = INDEX_DIR / "notes.index"
PATHS_FILE = INDEX_DIR / "notes.paths"


def load_embeddings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT path, embedding FROM notes")
    rows = cursor.fetchall()
    conn.close()

    paths = []
    vectors = []

    for path, blob in rows:
        vec = from_blob(blob)
        norm = np.linalg.norm(vec)
        if norm == 0:
            continue
        paths.append(path)
        vectors.append(vec)

    if not vectors:
        return [], np.array([])

    return paths, np.vstack(vectors).astype("float32")


def build_index(vectors: np.ndarray):
    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)
    return index


def save_index(index, paths):
    faiss.write_index(index, str(INDEX_FILE))
    with open(PATHS_FILE, "w") as f:
        json.dump(paths, f)


def load_index():
    if not INDEX_FILE.exists() or not PATHS_FILE.exists():
        return None, None
    try:
        index = faiss.read_index(str(INDEX_FILE))
        with open(PATHS_FILE) as f:
            paths = json.load(f)
        return paths, index
    except Exception:
        return None, None


def faiss_search(query_vec: np.ndarray, index, paths: list[str], k: int) -> list[dict]:
    scores, indices = index.search(query_vec, k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append({
            "path": paths[idx],
            "faiss_score": float(score)
        })
    return results
