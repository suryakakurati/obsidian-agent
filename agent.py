from vault_scan import add_all, scan_updates
from config import VAULT_PATH, DB_PATH


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