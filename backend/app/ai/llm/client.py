"""LLM Client - unified interface for all LLM operations."""

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.ai.llm.base import LLMProvider, LLMResponse, StructuredLLMResponse, EmbeddingResponse
from app.ai.llm.providers.openai_provider import OpenAIProvider
from app.ai.llm.providers.ollama_provider import OllamaProvider
from app.ai.llm.providers.fallback_provider import FallbackProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client with provider abstraction."""

    def __init__(self):
        self.provider = self._initialize_provider()
        self.ai_mode = settings.ai_mode.lower()
        logger.info(f"LLM Client initialized")
        logger.info(f"  Provider: {type(self.provider).__name__}")
        logger.info(f"  Model: {getattr(self.provider, 'model', 'N/A')}")
        logger.info(f"  AI Mode: {self.ai_mode}")
        logger.info(f"  Available: {self.provider.is_available()}")

    def _initialize_provider(self) -> LLMProvider:
        """Initialize LLM provider based on configuration."""
        # Demo mode always uses fallback
        if settings.ai_mode.lower() == "demo":
            logger.info("Demo mode enabled, using FallbackProvider")
            return FallbackProvider()
        
        provider_name = settings.llm_provider.lower()
        
        try:
            if provider_name == "ollama":
                logger.info(f"Initializing Ollama provider at {settings.ollama_base_url}")
                ollama_provider = OllamaProvider()
                if ollama_provider.is_available():
                    logger.info("Ollama provider available and ready")
                    return ollama_provider
                else:
                    logger.warning("Ollama not available, attempting fallback")
                    return FallbackProvider()
                    
            elif provider_name == "openai":
                logger.info("Initializing OpenAI provider")
                openai_provider = OpenAIProvider()
                if openai_provider.is_available():
                    logger.info("OpenAI provider available and ready")
                    return openai_provider
                else:
                    logger.warning("OpenAI not available, attempting fallback")
                    return FallbackProvider()
                    
            elif provider_name == "fallback":
                logger.info("Fallback provider explicitly selected")
                return FallbackProvider()
            else:
                logger.error(f"Unknown provider: {provider_name}, using fallback")
                return FallbackProvider()
                
        except Exception as e:
            logger.error(f"Error initializing provider: {e}, using fallback")
            return FallbackProvider()

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text from prompt."""
        try:
            return await self.provider.generate(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        schema: BaseModel,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> StructuredLLMResponse:
        """Generate structured output matching schema."""
        try:
            return await self.provider.generate_structured(prompt, schema, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding for text."""
        try:
            return await self.provider.embed(text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def is_available(self) -> bool:
        """Check if LLM provider is available."""
        return self.provider.is_available()

    def is_demo_mode(self) -> bool:
        """Check if using fallback/demo provider."""
        return isinstance(self.provider, FallbackProvider)

    async def health_check(self) -> Dict[str, Any]:
        """Get health status of LLM provider."""
        # Try to call provider's health check if available
        if hasattr(self.provider, "health_check"):
            return await self.provider.health_check()
        
        # Fallback health check
        return {
            "provider": type(self.provider).__name__,
            "reachable": self.provider.is_available(),
            "model": getattr(self.provider, "model", "N/A"),
        }


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

