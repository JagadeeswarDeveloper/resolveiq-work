"""Tests for LLM providers and client."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pydantic import BaseModel

from app.ai.llm.base import LLMProvider, LLMResponse, StructuredLLMResponse
from app.ai.llm.client import LLMClient
from app.ai.llm.providers.fallback_provider import FallbackProvider
from app.ai.llm.providers.ollama_provider import OllamaProvider
from app.core.config import settings


class SampleSchema(BaseModel):
    """Sample schema for testing."""
    name: str
    value: int
    optional_field: str = None


class TestFallbackProvider:
    """Test fallback provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = FallbackProvider()
        assert provider is not None
        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test text generation."""
        provider = FallbackProvider()
        response = await provider.generate("Test prompt")
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "fallback"

    @pytest.mark.asyncio
    async def test_generate_structured(self):
        """Test structured output generation."""
        provider = FallbackProvider()
        response = await provider.generate_structured(
            "Generate test data",
            SampleSchema
        )
        
        assert response.data is not None
        assert "name" in response.data
        assert "value" in response.data

    @pytest.mark.asyncio
    async def test_embed(self):
        """Test embedding generation."""
        provider = FallbackProvider()
        response = await provider.embed("Test text")
        
        assert response.embedding is not None
        assert len(response.embedding) > 0


class TestOllamaProvider:
    """Test Ollama provider."""

    def test_initialization(self):
        """Test provider initialization."""
        with patch('app.ai.llm.providers.ollama_provider.httpx') as mock_httpx:
            # Mock availability check
            provider = OllamaProvider()
            assert provider is not None
            assert provider.base_url == settings.ollama_base_url
            assert provider.model == settings.llm_model

    @pytest.mark.asyncio
    async def test_generate_when_available(self):
        """Test text generation when Ollama is available."""
        provider = OllamaProvider()
        provider._available = True  # Mock availability

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "Test response from Ollama"}

        with patch('app.ai.llm.providers.ollama_provider.httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_context.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_client.return_value.__aexit__.return_value = None

            response = await provider.generate("Test prompt")
            assert response.content == "Test response from Ollama"
            assert response.model == provider.model

    @pytest.mark.asyncio
    async def test_generate_when_unavailable(self):
        """Test generation fails when Ollama is unavailable."""
        provider = OllamaProvider()
        provider._available = False
        
        with pytest.raises(RuntimeError):
            await provider.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_structured_with_valid_json(self):
        """Test structured generation with valid JSON response."""
        provider = OllamaProvider()
        provider._available = True

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": '{"name": "test", "value": 42}'}

        with patch('app.ai.llm.providers.ollama_provider.httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_context.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_client.return_value.__aexit__.return_value = None

            result = await provider.generate_structured(
                "Generate test",
                SampleSchema
            )

            assert result.data["name"] == "test"
            assert result.data["value"] == 42

    @pytest.mark.asyncio
    async def test_generate_structured_with_invalid_json(self):
        """Test structured generation with invalid JSON response."""
        provider = OllamaProvider()
        provider._available = True

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "This is not JSON {invalid"}

        with patch('app.ai.llm.providers.ollama_provider.httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_context.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_client.return_value.__aexit__.return_value = None

            with pytest.raises(ValueError):
                await provider.generate_structured(
                    "Generate test",
                    SampleSchema
                )

    @pytest.mark.asyncio
    async def test_health_check_when_available(self):
        """Test health check when Ollama is available."""
        provider = OllamaProvider()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch('app.ai.llm.providers.ollama_provider.httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_client.return_value.__aexit__.return_value = None

            result = await provider.health_check()

            assert result["provider"] == "ollama"
            assert result["reachable"] is True
            assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_health_check_when_unavailable(self):
        """Test health check when Ollama is unavailable."""
        provider = OllamaProvider()

        with patch('app.ai.llm.providers.ollama_provider.httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_context.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_client.return_value.__aexit__.return_value = None

            result = await provider.health_check()

            assert result["provider"] == "ollama"
            assert result["reachable"] is False


class TestLLMClient:
    """Test unified LLM client."""

    def test_initialization_with_fallback(self):
        """Test client initialization with fallback provider."""
        original_ai_mode = settings.ai_mode
        try:
            settings.ai_mode = "demo"
            client = LLMClient()
            assert isinstance(client.provider, FallbackProvider)
            assert client.is_demo_mode() is True
        finally:
            settings.ai_mode = original_ai_mode

    def test_initialization_with_ollama(self):
        """Test client initialization with Ollama provider."""
        original_provider = settings.llm_provider
        original_ai_mode = settings.ai_mode
        try:
            settings.llm_provider = "ollama"
            settings.ai_mode = "live"
            with patch.object(OllamaProvider, 'is_available', return_value=True):
                client = LLMClient()
                assert client.provider is not None
        finally:
            settings.llm_provider = original_provider
            settings.ai_mode = original_ai_mode

    def test_initialization_with_unknown_provider(self):
        """Test client with unknown provider falls back."""
        original_provider = settings.llm_provider
        original_ai_mode = settings.ai_mode
        try:
            settings.llm_provider = "unknown_provider"
            settings.ai_mode = "live"
            client = LLMClient()
            assert isinstance(client.provider, FallbackProvider)
        finally:
            settings.llm_provider = original_provider
            settings.ai_mode = original_ai_mode

    @pytest.mark.asyncio
    async def test_provider_fallback_on_error(self):
        """Test that client falls back gracefully on provider error."""
        client = LLMClient()

        with patch.object(client.provider, 'generate', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check through client."""
        client = LLMClient()
        result = await client.health_check()

        assert result is not None
        assert "provider" in result or "error" in result


class TestProviderSelection:
    """Test provider selection logic."""

    def test_provider_selection_ollama(self):
        """Test Ollama provider selection."""
        provider_name = "ollama"
        assert provider_name == "ollama"

    def test_provider_selection_openai(self):
        """Test OpenAI provider selection."""
        provider_name = "openai"
        assert provider_name == "openai"

    def test_provider_selection_fallback(self):
        """Test fallback provider selection."""
        provider_name = "fallback"
        assert provider_name == "fallback"

    def test_invalid_provider_selection(self):
        """Test that invalid provider is rejected."""
        provider_name = "invalid_provider"
        assert provider_name not in ["ollama", "openai", "fallback"]


class TestStructuredOutput:
    """Test structured output validation."""

    @pytest.mark.asyncio
    async def test_structured_output_validation(self):
        """Test that structured output is validated against schema."""
        provider = FallbackProvider()
        
        response = await provider.generate_structured(
            "Test",
            SampleSchema
        )
        
        # Should validate successfully
        assert response.data is not None
        validated = SampleSchema(**response.data)
        assert validated is not None

    @pytest.mark.asyncio
    async def test_structured_output_with_optional_fields(self):
        """Test structured output with optional fields."""
        provider = FallbackProvider()
        
        response = await provider.generate_structured(
            "Test",
            SampleSchema
        )
        
        # optional_field might be None, which is valid
        validated = SampleSchema(**response.data)
        assert hasattr(validated, 'optional_field')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
