from pathlib import Path
import sqlite3
import numpy as np
import faiss

from llm import generate_embedding
from vector import from_blob, normalize
from db import DB_PATH

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

        # safety check (should already be normalized)
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


def search(query: str, k: int = 5):
    # 1. embed query
    query_vec = generate_embedding(query)

    if not query_vec:
        return []

    # 2. normalize query (IMPORTANT)
    query_vec = normalize(query_vec).astype("float32")

    query_vec = np.expand_dims(query_vec, axis=0)

    # 3. load data
    paths, vectors = load_embeddings()

    if len(paths) == 0:
        return []

    # 4. build index
    index = build_index(vectors)

    # 5. search
    scores, indices = index.search(query_vec, k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        results.append({
            "path": paths[idx],
            "score": float(score)
        })

    return results