import hashlib
import numpy as np
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class DeterministicFastEmbedding(EmbeddingFunction):
    """
    Fast, deterministic offline embedding function for vector memory.
    Maps arbitrary text to a normalized 128-dimensional dense vector
    without requiring external model downloads or network access.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def name(self) -> str:
        return "deterministic_fast_embedding"

    def get_config(self) -> dict:
        return {"dimension": self.dimension}

    def __call__(self, input: Documents) -> Embeddings:
        results = []
        for doc in input:
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = doc.lower().replace("_", " ").split()
            if not words:
                results.append(vec.tolist())
                continue

            for word in words:
                # Hash word to dimension index
                h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dimension
                # Weight by word length
                vec[idx] += 1.0 + (len(word) * 0.1)

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results
