from pathlib import Path
import sqlite3
import numpy as np
import faiss
import json

from llm import generate_embedding
from vector import from_blob, normalize
from db import DB_PATH


from config import VAULT_PATH

INDEX_DIR = Path(DB_PATH).parent
INDEX_FILE = INDEX_DIR / "notes.index"
PATHS_FILE = INDEX_DIR / "notes.paths"

def get_note_content(note_name: str):
    for file_path in VAULT_PATH.rglob("*.md"):
        if file_path.name == note_name:
            return file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

    return None

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


def build_and_persist_index():
    paths, vectors = load_embeddings()
    if len(paths) == 0:
        return
    index = build_index(vectors)
    save_index(index, paths)
    print(f"FAISS index persisted ({len(paths)} vectors)")


def search(query: str, k: int = 5):
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

    # search
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