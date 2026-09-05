"""LLM abstraction base classes."""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Response from LLM."""
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None


class StructuredLLMResponse(BaseModel):
    """Structured response from LLM."""
    data: Dict[str, Any]
    tokens_used: Optional[int] = None
    model: Optional[str] = None


class EmbeddingResponse(BaseModel):
    """Embedding response from LLM."""
    embedding: list[float]
    model: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text from prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: BaseModel,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> StructuredLLMResponse:
        """Generate structured output matching schema."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding for text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
