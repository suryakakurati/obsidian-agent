from config import OLLAMA_URL, OLLAMA_EMBED_MODEL
import requests
import numpy as np


def generate_embedding(text: str) -> list[float]:
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text
    }

    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json=payload,
            timeout=60
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out after 60s")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_URL}: {e}")

    if res.status_code != 200:
        raise RuntimeError(
            f"Ollama API returned {res.status_code}: {res.text[:200]}"
        )

    try:
        data = res.json()
    except ValueError as e:
        raise RuntimeError(f"Ollama returned invalid JSON: {e}")

    if "embedding" not in data:
        raise RuntimeError(
            f"Ollama response missing 'embedding' key. Keys: {list(data.keys())}"
        )

    embedding = data["embedding"]
    if (
        not isinstance(embedding, list)
        or not all(isinstance(v, (int, float)) for v in embedding)
    ):
        raise RuntimeError(
            f"Ollama returned malformed embedding "
            f"(type={type(embedding).__name__})"
        )

    return embedding
