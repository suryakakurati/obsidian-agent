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


PROGRESS_INTERVAL = 1000


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

    print(
        f"\nIndexing completed in "
        f"{time.time() - start_time:.2f} seconds.\n"
    )


def scan_updates(vault_path: Path = VAULT_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    changed_files = []
    batch = []

    start_time = time.time()

    processed = 0
    total_embedding_time = 0.0

    try:
        for file_path in vault_path.rglob("*.md"):
            cursor.execute(
                "SELECT hash, last_modified FROM notes WHERE path = ?",
                (str(file_path),)
            )

            row = cursor.fetchone()
            new_mtime = file_path.stat().st_mtime

            if row is None:
                file_hash = get_file_hash(file_path)

                record, embedding_time = build_note_record(
                    file_path,
                    file_hash
                )

                batch.append(record)

                changed_files.append(file_path)

                processed += 1
                total_embedding_time += embedding_time

                continue

            old_hash, old_mtime = row

            if new_mtime <= old_mtime:
                continue

            file_hash = get_file_hash(file_path)

            if file_hash != old_hash:
                record, embedding_time = build_note_record(
                    file_path,
                    file_hash
                )

                batch.append(record)

                changed_files.append(file_path)

                processed += 1
                total_embedding_time += embedding_time

                if processed % PROGRESS_INTERVAL == 0:
                    elapsed = time.time() - start_time

                    avg_note_time = elapsed / processed
                    avg_embedding_time = (
                        total_embedding_time / processed
                    )

                    print(
                        f"\n[{processed:,} notes] "
                        f"avg/note={avg_note_time:.4f}s "
                        f"avg/embed={avg_embedding_time:.4f}s\n"
                    )

        if batch:
            upsert_notes_batch(batch, conn)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    print(
        f"\nScan completed in "
        f"{time.time() - start_time:.2f} seconds.\n"
    )

    return changed_files