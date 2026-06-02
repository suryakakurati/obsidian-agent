from pathlib import Path
import sqlite3
import hashlib
from llm import generate_embedding
from vector import normalize, to_blob
from config import DB_PATH


def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        hash TEXT,
        embedding BLOB,
        last_modified REAL
    )
    """)

    conn.commit()
    conn.close()


def get_file_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def upsert_note(file_path: Path, conn: sqlite3.Connection, file_hash: str):
    cursor = conn.cursor()

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    embedding_vec = generate_embedding(content)
    embedding_vec = normalize(embedding_vec)
    embedding_blob = to_blob(embedding_vec)

    last_modified = file_path.stat().st_mtime

    cursor.execute("""
        INSERT INTO notes (path, hash, embedding, last_modified)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            hash=excluded.hash,
            embedding=excluded.embedding,
            last_modified=excluded.last_modified
    """, (
        str(file_path),
        file_hash,
        embedding_blob,
        last_modified
    ))

