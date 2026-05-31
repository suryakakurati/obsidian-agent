from pathlib import Path
import sqlite3
import hashlib

DB_PATH = Path("data/vault.db")


def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        hash TEXT,
        summary TEXT,
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
    summary = content[:300]
    last_modified = file_path.stat().st_mtime

    cursor.execute("""
        INSERT INTO notes (path, hash, summary, last_modified)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            hash=excluded.hash,
            summary=excluded.summary,
            last_modified=excluded.last_modified
    """, (
        str(file_path),
        file_hash,
        summary,
        last_modified
    ))