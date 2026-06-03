from config import OLLAMA_MODEL, OLLAMA_URL
import requests
import numpy as np


def generate_embedding(text: str) -> list[float]:
    payload = {
        "model": "nomic-embed-text",
        "prompt": text
    }

    res = requests.post(f"{OLLAMA_URL}/api/embeddings", json=payload, timeout=60)
    data = res.json()
    return data["embedding"]