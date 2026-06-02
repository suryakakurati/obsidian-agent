from config import OLLAMA_MODEL, OLLAMA_URL
import requests
import numpy as np


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
