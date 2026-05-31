from pathlib import Path
import sqlite3

from db import(
    DB_PATH,
    initialize_db,
    upsert_note,
    get_file_hash
)

from config import VAULT_PATH

def add_all(vault_path: Path = VAULT_PATH):
    initialize_db()
    conn = sqlite3.connect(DB_PATH)

    for file_path in vault_path.rglob("*.md"):
        file_hash = get_file_hash(file_path)
        print("Indexing:", file_path)

        upsert_note(file_path, conn, file_hash)

    conn.commit()
    conn.close()

def scan_updates(vault_path: Path = VAULT_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    changed_files = []

    for file_path in vault_path.rglob("*.md"):
        cursor.execute(
            "SELECT hash, last_modified FROM notes WHERE path = ?",
            (str(file_path),)
        )

        row = cursor.fetchone()

        new_mtime = file_path.stat().st_mtime

        if row is None:
            file_hash = get_file_hash(file_path)
            upsert_note(file_path, conn, file_hash)
            changed_files.append(file_path)
            continue

        old_hash, old_mtime = row

        
        if new_mtime <= old_mtime:
            continue

        file_hash = get_file_hash(file_path)

        if file_hash != old_hash:
            upsert_note(file_path, conn, file_hash)
            changed_files.append(file_path)

    conn.commit()
    conn.close()

    return changed_files