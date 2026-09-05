import os

import pytest
from pydantic import BaseModel

from app.ai.llm.providers.ollama_provider import OllamaProvider


class OllamaSmokeSchema(BaseModel):
    answer: str


@pytest.mark.skipif(os.getenv("OLLAMA_TEST", "false").lower() != "true", reason="Set OLLAMA_TEST=true to run")
@pytest.mark.asyncio
async def test_ollama_structured_response():
    provider = OllamaProvider()
    if not provider.is_available():
        pytest.fail("Ollama is unavailable; start Ollama and install the configured model")
    response = await provider.generate_structured(
        'Return JSON only with an answer field containing "ok".',
        OllamaSmokeSchema,
    )
    assert OllamaSmokeSchema(**response.data).answer
