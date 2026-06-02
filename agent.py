from vault_scan import add_all, scan_updates
from config import VAULT_PATH, DB_PATH
from retrieval import search, get_note_content


def similar_notes(note_name: str):

    if not DB_PATH.exists():
        print("Database not found. Please run the agent to index the vault first.")
        return
    if not note_name.endswith(".md"):
        note_name += ".md"
    content = get_note_content(note_name)

    if content:
        results = search(content)
        for r in results:
            print(r)
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