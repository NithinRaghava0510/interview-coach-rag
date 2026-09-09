import hashlib
import math
import re

from openai import OpenAI

from app.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.client and not settings.demo_mode:
            response = self.client.embeddings.create(model=settings.embedding_model, input=texts)
            return [item.embedding for item in response.data]
        return [self._demo_embedding(text) for text in texts]

    def _demo_embedding(self, text: str) -> list[float]:
        # Deterministic hashing vector so the complete RAG flow works without paid APIs.
        vector = [0.0] * settings.embedding_dimensions
        for token in re.findall(r"[a-z0-9+#.]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % settings.embedding_dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


embedding_service = EmbeddingService()
