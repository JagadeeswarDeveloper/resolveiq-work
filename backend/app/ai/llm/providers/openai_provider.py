"""OpenAI provider implementation."""

import json
import logging
from typing import Optional
from pydantic import BaseModel

from app.ai.llm.base import LLMProvider, LLMResponse, StructuredLLMResponse, EmbeddingResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.llm_model
        self.client = None
        
        if self.api_key:
            try:
                import openai
                openai.api_key = self.api_key
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI library not installed")

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text from prompt."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens or 1000,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=self.model,
            )
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        schema: BaseModel,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> StructuredLLMResponse:
        """Generate structured output matching schema."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")

        try:
            # Build JSON schema from Pydantic model
            json_schema = schema.model_json_schema()
            
            system_prompt = f"""You are a JSON API. Return ONLY valid JSON matching this schema:
{json.dumps(json_schema, indent=2)}

Do not include any text outside the JSON. Return only the JSON object."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens or 2000,
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {content}")
                raise ValueError(f"Invalid JSON response from LLM")
            
            return StructuredLLMResponse(
                data=data,
                tokens_used=response.usage.total_tokens,
                model=self.model,
            )
        except Exception as e:
            logger.error(f"OpenAI structured generation error: {e}")
            raise

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding for text."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")

        try:
            response = await self.client.embeddings.create(
                model=settings.embedding_model,
                input=text,
            )
            
            return EmbeddingResponse(
                embedding=response.data[0].embedding,
                model=settings.embedding_model,
            )
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.client is not None and self.api_key is not None
