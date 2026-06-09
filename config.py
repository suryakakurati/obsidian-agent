from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
if not OLLAMA_URL:
    raise ValueError("OLLAMA_URL is required. Set it in .env")

VAULT_PATH = os.getenv("VAULT_PATH")
if not VAULT_PATH:
    raise ValueError("VAULT_PATH is required. Set it in .env")
VAULT_PATH = Path(VAULT_PATH)

DB_PATH = os.getenv("DB_PATH")
if not DB_PATH:
    raise ValueError("DB_PATH is required. Set it in .env")
DB_PATH = Path(DB_PATH)
if not DB_PATH.is_absolute():
    DB_PATH = Path.cwd() / DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
