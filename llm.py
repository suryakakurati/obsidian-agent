from config import OLLAMA_MODEL, OLLAMA_URL
import requests
import numpy as np

SYSTEM_PROMPT = """
You are summarizing an Obsidian note for retrieval purposes.

Write a concise summary (2-5 sentences) that:
- Preserves important concepts and terminology.
- Includes technical keywords when relevant.
- Mentions major definitions, relationships, and topics.
- Avoids filler language.
"""

def generate_summary(text: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": SYSTEM_PROMPT + "\n\nNote:\n" + text,
        "stream": False,
        "options": {"temperature": 0.1},
        "keep_alive": "2m"
    }

    try:
        res = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        data = res.json()
        return data["response"].strip()

    except Exception as e:
        print(f"Summary generation failed: {e}")
        return text[:300]
def generate_embedding(text: str) -> list[float]:
    payload = {
        "model": "nomic-embed-text",
        "prompt": text
    }

    try:
        res = requests.post(f"{OLLAMA_URL}/api/embeddings", json=payload, timeout=60)
        data = res.json()
        return data["embedding"]

    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return []

def to_blob(vec):
    return np.array(vec, dtype=np.float32).tobytes()


def from_blob(blob):
    return np.frombuffer(blob, dtype=np.float32)
