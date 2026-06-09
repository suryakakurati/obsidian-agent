from vault_scan import add_all, scan_updates, get_note_content
from config import VAULT_PATH, DB_PATH
from retrieval import search, filter_by_tiers
import sqlite3


def print_similar(results: list[dict]):
    if not results:
        print("No similar notes found.")
        return
    print(f"{'Note':<40} {'FAISS':<8} {'BM25':<8} {'Hybrid':<8}")
    print("-" * 68)
    for r in results:
        name = r["name"]
        faiss = r["faiss"]
        bm25 = r["bm25"]
        hybrid = r["hybrid"]
        print(f"{name:<40} {faiss:<8.4f} {bm25:<8.2f} {hybrid:<8.4f}")


def similar_notes(note_name: str, k: int = 5):

    if not DB_PATH.exists():
        print("Database not found. Please run the agent to index the vault first.")
        return
    if not note_name.endswith(".md"):
        note_name += ".md"
    content = get_note_content(note_name)

    if content:
        conn = sqlite3.connect(DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        conn.close()
        results = search(content, k=n)
        filtered = filter_by_tiers(results, top_k=k)
        print_similar(filtered)
    else:
        print("Note not found.")


def first_run():
    add_all()
    print("Vault indexed.")

def maintenance():
    changed_files = scan_updates()

    if changed_files:
        print("Updated files:")
        for file in changed_files:
            print("-", file)
    else:
        print("No changes detected.")

if __name__ == "__main__":
    if not DB_PATH.exists():
        first_run()
    else:
        maintenance()