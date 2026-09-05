"""Configurable embedding providers with a deterministic local fallback."""

import hashlib
import math
from typing import Protocol

from app.ai.llm.providers.ollama_provider import OllamaProvider
from app.core.config import settings


class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class HashEmbeddingProvider:
    """Small deterministic vectorizer for local tests and offline development."""

    def __init__(self, dimension: int | None = None):
        self.dimension = dimension or settings.embedding_dimension

    async def embed(self, text: str) -> list[float]:
        values = [0.0] * self.dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            values[index] += 1.0
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]


class OllamaEmbeddingProvider:
    def __init__(self):
        self.provider = OllamaProvider()
        self.fallback = HashEmbeddingProvider()

    async def embed(self, text: str) -> list[float]:
        try:
            return (await self.provider.embed(text)).embedding
        except Exception:
            return await self.fallback.embed(text)


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider.lower() == "ollama":
        provider = OllamaEmbeddingProvider()
        if provider.provider.is_available():
            return provider
    return HashEmbeddingProvider()
