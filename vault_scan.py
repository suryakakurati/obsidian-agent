from pathlib import Path
import sqlite3
import time
from db import (
    DB_PATH,
    initialize_db,
    get_file_hash,
    build_note_record,
    upsert_notes_batch
)

from config import VAULT_PATH

def add_all(vault_path: Path = VAULT_PATH):
    initialize_db()
    conn = sqlite3.connect(DB_PATH)
    start_time = time.time()

    batch = []
    batch_size = 50

    for file_path in vault_path.rglob("*.md"):
        file_hash = get_file_hash(file_path)
        print("Indexing:", file_path)

        record = build_note_record(file_path, file_hash)
        batch.append(record)

        if len(batch) >= batch_size:
            upsert_notes_batch(batch, conn)
            batch = []

    if batch:
        upsert_notes_batch(batch, conn)

    conn.commit()
    conn.close()

    print(f"Indexing completed in {time.time() - start_time:.2f} seconds.")

def scan_updates(vault_path: Path = VAULT_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    changed_files = []
    batch = []

    start_time = time.time()

    for file_path in vault_path.rglob("*.md"):
        cursor.execute(
            "SELECT hash, last_modified FROM notes WHERE path = ?",
            (str(file_path),)
        )

        row = cursor.fetchone()
        new_mtime = file_path.stat().st_mtime

        if row is None:
            file_hash = get_file_hash(file_path)
            print("Indexing:", file_path)

            batch.append(build_note_record(file_path, file_hash))
            changed_files.append(file_path)
            continue

        old_hash, old_mtime = row

        if new_mtime <= old_mtime:
            continue

        file_hash = get_file_hash(file_path)

        if file_hash != old_hash:
            batch.append(build_note_record(file_path, file_hash))
            changed_files.append(file_path)

    if batch:
        upsert_notes_batch(batch, conn)

    conn.commit()
    conn.close()

    print(f"Scan completed in {time.time() - start_time:.2f} seconds.")

    return changed_files