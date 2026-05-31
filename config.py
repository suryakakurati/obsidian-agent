from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_URL = os.getenv("OLLAMA_URL")

VAULT_PATH = Path(os.getenv("VAULT_PATH"))

DB_PATH = Path(os.getenv("DB_PATH"))