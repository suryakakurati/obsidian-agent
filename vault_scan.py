from pathlib import Path
import sqlite3
import time

from db import (
    initialize_db,
    get_file_hash,
    build_note_record,
    upsert_notes_batch
)


from config import VAULT_PATH, DB_PATH
from retrieval import build_and_persist_index


PROGRESS_INTERVAL = 10


def add_all(vault_path: Path = VAULT_PATH):
    initialize_db()

    conn = sqlite3.connect(DB_PATH)

    start_time = time.time()

    batch = []
    batch_size = 100

    processed = 0
    total_embedding_time = 0.0

    try:
        for file_path in vault_path.rglob("*.md"):
            file_hash = get_file_hash(file_path)

            record, embedding_time = build_note_record(
                file_path,
                file_hash
            )

            batch.append(record)

            processed += 1
            total_embedding_time += embedding_time

            if processed % PROGRESS_INTERVAL == 0:
                elapsed = time.time() - start_time

                avg_note_time = elapsed / processed
                avg_embedding_time = total_embedding_time / processed

                print(
                    f"\n[{processed:,} notes] "
                    f"avg/note={avg_note_time:.4f}s "
                    f"avg/embed={avg_embedding_time:.4f}s\n"
                )

            if len(batch) >= batch_size:
                upsert_notes_batch(batch, conn)
                batch = []

        if batch:
            upsert_notes_batch(batch, conn)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    try:
        build_and_persist_index()
    except Exception as e:
        print(f"Warning: Failed to persist FAISS index: {e}")

    print(
        f"\nIndexing completed in "
        f"{time.time() - start_time:.2f} seconds.\n"
    )


def _handle_file(file_path: Path, cursor: sqlite3.Cursor):
    cursor.execute(
        "SELECT hash, last_modified FROM notes WHERE path = ?",
        (str(file_path),)
    )
    row = cursor.fetchone()
    new_mtime = file_path.stat().st_mtime

    if row is None:
        file_hash = get_file_hash(file_path)
        record, embedding_time = build_note_record(file_path, file_hash)
        return record, embedding_time, True

    old_hash, old_mtime = row

    if new_mtime <= old_mtime:
        return None, 0, False

    file_hash = get_file_hash(file_path)

    if file_hash != old_hash:
        record, embedding_time = build_note_record(file_path, file_hash)
        return record, embedding_time, False

    return None, 0, False


def _print_progress(processed: int, start_time: float, total_embedding_time: float):
    elapsed = time.time() - start_time
    avg_note_time = elapsed / processed
    avg_embedding_time = total_embedding_time / processed
    print(
        f"\n[{processed:,} notes] "
        f"avg/note={avg_note_time:.4f}s "
        f"avg/embed={avg_embedding_time:.4f}s\n"
    )


def scan_updates(vault_path: Path = VAULT_PATH):
    initialize_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    changed_files = []
    batch = []
    disk_paths = set()
    deleted_paths = []

    start_time = time.time()
    processed = 0
    total_embedding_time = 0.0

    try:
        for file_path in vault_path.rglob("*.md"):
            disk_paths.add(str(file_path))
            record, embedding_time, is_new = _handle_file(file_path, cursor)

            if record is None:
                continue

            batch.append(record)
            changed_files.append(file_path)
            processed += 1
            total_embedding_time += embedding_time

            if processed % PROGRESS_INTERVAL == 0 and not is_new:
                _print_progress(processed, start_time, total_embedding_time)

        cursor.execute("SELECT path FROM notes")
        deleted_paths = [
            row[0] for row in cursor.fetchall()
            if row[0] not in disk_paths
        ]

        if deleted_paths:
            chunk_size = 999
            for i in range(0, len(deleted_paths), chunk_size):
                chunk = deleted_paths[i:i + chunk_size]
                placeholders = ",".join("?" for _ in chunk)
                cursor.execute(
                    f"DELETE FROM notes WHERE path IN ({placeholders})",
                    chunk
                )

        if batch:
            upsert_notes_batch(batch, conn)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    if changed_files or deleted_paths:
        try:
            build_and_persist_index()
        except Exception as e:
            print(f"Warning: Failed to persist FAISS index: {e}")

    print(
        f"\nScan completed in "
        f"{time.time() - start_time:.2f} seconds.\n"
    )

    changed_files.extend(deleted_paths)
    return changed_files