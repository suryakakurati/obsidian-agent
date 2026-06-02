import numpy as np

def normalize(vec: list[float]) -> np.ndarray:
    v = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(v)

    if norm == 0:
        return v

    return v / norm

def to_blob(vec):
    return np.array(vec, dtype=np.float32).tobytes()


def from_blob(blob):
    return np.frombuffer(blob, dtype=np.float32)
