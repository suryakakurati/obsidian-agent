from config import OLLAMA_MODEL, OLLAMA_URL
import requests

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
        res = requests.post(OLLAMA_URL, json=payload, timeout=60)
        data = res.json()
        return data["response"].strip()

    except Exception as e:
        print(f"Summary generation failed: {e}")
        return text[:300]