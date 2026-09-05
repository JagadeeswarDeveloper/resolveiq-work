"""Ollama LLM Provider - local LLM support via Ollama API."""

import logging
import json
import asyncio
from typing import Optional, Any, Dict
from datetime import datetime
import httpx
from pydantic import BaseModel

from app.ai.llm.base import LLMProvider, LLMResponse, StructuredLLMResponse, EmbeddingResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama LLM provider using local HTTP API."""

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.llm_model
        self.embedding_model = settings.embedding_model
        self.timeout = 300  # 5 minutes for long completions
        self._available = None
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Ollama is reachable."""
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            self._available = response.status_code == 200
            if self._available:
                logger.info(f"Ollama available at {self.base_url}")
                logger.info(f"Using model: {self.model}")
            else:
                logger.warning(f"Ollama returned status {response.status_code}")
                self._available = False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if Ollama provider is available."""
        return self._available is True

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text from prompt using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama provider not available")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                }
                
                if max_tokens:
                    payload["num_predict"] = max_tokens

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                
                result = response.json()
                
                return LLMResponse(
                    content=result.get("response", ""),
                    tokens_used=None,  # Ollama API doesn't expose token counts
                    model=self.model,
                )

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> StructuredLLMResponse:
        """Generate structured output matching Pydantic schema."""
        if not self.is_available():
            raise RuntimeError("Ollama provider not available")

        # Build a prompt that encourages JSON output
        json_schema = schema.model_json_schema()
        
        structured_prompt = f"""{prompt}

RESPONSE FORMAT:
Return ONLY valid JSON matching this schema, no markdown, no explanation:

{json.dumps(json_schema, indent=2)}

Ensure all required fields are present. Use null for optional fields if unknown.
Do not invent information not in the context.
"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": structured_prompt,
                    "stream": False,
                    "temperature": temperature,
                    "format": "json",
                }
                
                if max_tokens:
                    payload["num_predict"] = max_tokens

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                
                result = response.json()
                content = result.get("response", "").strip()
                
                # Parse JSON response
                try:
                    # Try to extract JSON from response
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        data = json.loads(json_str)
                    else:
                        logger.warning(f"No JSON found in response: {content[:100]}")
                        raise ValueError("No JSON in response")
                    
                    # Validate against schema
                    validated = schema(**data)
                    
                    return StructuredLLMResponse(
                        data=validated.model_dump(exclude_none=False),
                        tokens_used=None,
                        model=self.model,
                    )
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    logger.error(f"Response was: {content[:200]}")
                    raise ValueError(f"Invalid JSON in LLM response: {e}")
                except Exception as e:
                    logger.error(f"Schema validation error: {e}")
                    raise

        except Exception as e:
            logger.error(f"Ollama structured generation error: {e}")
            raise

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama provider not available")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                payload = {
                    "model": self.embedding_model,
                    "prompt": text,
                }

                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                
                result = response.json()
                
                return EmbeddingResponse(
                    embedding=result.get("embedding", []),
                    model=self.embedding_model,
                )

        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Health check for Ollama."""
        try:
            start_time = datetime.utcnow()
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                if response.status_code == 200:
                    return {
                        "provider": "ollama",
                        "model": self.model,
                        "reachable": True,
                        "latency_ms": latency_ms,
                        "base_url": self.base_url,
                    }
                else:
                    return {
                        "provider": "ollama",
                        "model": self.model,
                        "reachable": False,
                        "latency_ms": latency_ms,
                        "error": f"Status {response.status_code}",
                    }
                    
        except Exception as e:
            return {
                "provider": "ollama",
                "model": self.model,
                "reachable": False,
                "error": str(e),
            }
