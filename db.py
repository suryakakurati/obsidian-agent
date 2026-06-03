from pathlib import Path
import sqlite3
import hashlib
import time

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


def build_note_record(file_path: Path, file_hash: str):
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    embed_start = time.time()

    try:
        embedding_vec = generate_embedding(content)
    except Exception as e:
        print(f"\nERROR embedding {file_path}: {e}\n")
        raise

    embedding_time = time.time() - embed_start

    embedding_vec = normalize(embedding_vec)
    embedding_blob = to_blob(embedding_vec)

    last_modified = file_path.stat().st_mtime

    record = (
        str(file_path),
        file_hash,
        embedding_blob,
        last_modified
    )

    return record, embedding_time


def upsert_notes_batch(records, conn: sqlite3.Connection):
    cursor = conn.cursor()

    try:
        cursor.execute("SAVEPOINT upsert_batch")

        cursor.executemany("""
            INSERT INTO notes (path, hash, embedding, last_modified)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                hash=excluded.hash,
                embedding=excluded.embedding,
                last_modified=excluded.last_modified
        """, records)

        cursor.execute("RELEASE SAVEPOINT upsert_batch")

    except sqlite3.Error:
        cursor.execute("ROLLBACK TO SAVEPOINT upsert_batch")
        raise