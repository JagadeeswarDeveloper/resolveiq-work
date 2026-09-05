# ResolveIQ Phase 2.5: Ollama Integration

## Overview

Ollama is now **the default LLM provider** for local development and hackathon use. This document explains the architecture, setup, and usage.

## Architecture

### Provider Hierarchy

```
Agent (UnderstandingAgent, ResolutionAgent, SupervisorAgent)
        ↓
   LLMClient (unified interface)
        ↓
    ┌───┴────┬───────┐
    ↓        ↓       ↓
 Ollama    OpenAI  Fallback
(local)  (cloud)  (demo)
```

### How It Works

1. **LLMClient** initializes based on `LLM_PROVIDER` environment variable
2. **Ollama Provider** connects to Ollama HTTP API at `OLLAMA_BASE_URL`
3. If Ollama unreachable → **Fallback Provider** automatically activates
4. **Same code path** for all agents regardless of provider
5. All operations logged to `agent_executions` table with provider info

## Setup

### Prerequisites

1. **Ollama installed** - Download from https://ollama.ai
2. **Models pulled** - Run: `ollama pull neural-chat` and `ollama pull nomic-embed-text`
3. **Ollama running** - `ollama serve` (default: localhost:11434)

### Option 1: Local Development (Recommended for Hackathon)

Host Ollama, containerized backend:

```bash
# 1. Start Ollama on host
ollama serve

# 2. Pull recommended model (one-time)
ollama pull neural-chat
ollama pull nomic-embed-text

# 3. Start backend services
docker-compose up -d postgres redis frontend

# 4. Start backend (connects to host Ollama)
docker-compose up -d backend

# 5. Verify
curl http://localhost:8000/api/v1/system/llm-status
```

ResolveIQ uses `neural-chat` for chat generation and `nomic-embed-text` for RAG embeddings. The embedding model returns 768-dimensional vectors, so `EMBEDDING_DIMENSION` must be `768`. ResolveIQ calls Ollama's `/api/embeddings` endpoint. If Ollama or the embedding model is unavailable, RAG falls back to deterministic hash embeddings.

**Note for Windows**: Docker automatically maps `host.docker.internal:11434` for host access

### Option 2: Everything in Docker

Uncomment Ollama service in docker-compose.yml:

```bash
# Uncomment ollama service and volume
# In backend environment: OLLAMA_BASE_URL=http://ollama:11434

docker-compose up -d
```

### Configuration

**.env or environment variables:**

```bash
# Provider selection
LLM_PROVIDER=ollama              # Default for development
LLM_MODEL=neural-chat           # Ollama model to use
OLLAMA_BASE_URL=http://localhost:11434

# For demo/testing (no Ollama needed)
LLM_PROVIDER=fallback
AI_MODE=demo

# For production (if using OpenAI)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=sk-...
```

## Recommended Models

### General Purpose (Balanced)
- **`neural-chat:latest`** - 7B, balanced quality/speed (RECOMMENDED)
  - ```bash
    ollama pull neural-chat
    ```

### Smaller/Faster
- **`mistral:latest`** - 7B, very fast
  - ```bash
    ollama pull mistral
    ```

### Larger/Smarter
- **`llama2:latest`** - 7B, good reasoning
  - ```bash
    ollama pull llama2
    ```

### Embeddings (for future RAG)
- **`nomic-embed-text:latest`** - Specialized embeddings
  - ```bash
    ollama pull nomic-embed-text
    ```

**Note**: For hackathon, start with `neural-chat` - good balance of quality and speed.

## Monitoring

### LLM Status Endpoint

```bash
curl http://localhost:8000/api/v1/system/llm-status
```

Response:

```json
{
  "provider": "ollama",
  "model": "neural-chat",
  "reachable": true,
  "latency_ms": 125,
  "base_url": "http://localhost:11434",
  "ai_mode": "live"
}
```

Or if Ollama is down:

```json
{
  "provider": "ollama",
  "model": "neural-chat",
  "reachable": false,
  "error": "Connection refused"
}
```

### System Info Endpoint

```bash
curl http://localhost:8000/api/v1/system/system-info
```

Shows LLM status, database stats, and environment info.

### Agent Execution Logs

```sql
-- See which provider was used
SELECT 
    agent_name,
    model_used,
    provider_used,
    AVG(latency_ms) as avg_latency,
    COUNT(*) as total_calls
FROM agent_executions
GROUP BY agent_name, model_used, provider_used
ORDER BY COUNT(*) DESC;

-- Check for fallback usage (when Ollama was down)
SELECT * FROM agent_executions 
WHERE model_used = 'fallback' 
ORDER BY started_at DESC;
```

## Workflow

### End-to-End with Ollama

```bash
# 1. Create complaint
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "raw_text": "My order arrived damaged!",
    "customer_email": "test@example.com"
  }' | jq '.data.id' > complaint_id.txt

COMPLAINT_ID=$(cat complaint_id.txt)

# 2. Analyze (UnderstandingAgent + Ollama)
curl -X POST http://localhost:8000/api/v1/complaints/$COMPLAINT_ID/analyze

# 3. Generate resolution (ResolutionAgent + Ollama)
curl -X POST http://localhost:8000/api/v1/complaints/$COMPLAINT_ID/resolve

# 4. Route (SupervisorAgent + Ollama)
curl -X POST http://localhost:8000/api/v1/complaints/$COMPLAINT_ID/route

# 5. Check LLM status
curl http://localhost:8000/api/v1/system/llm-status | jq .
```

## Fallback Behavior

### What Happens When Ollama is Unavailable

1. **Request to Ollama** → Timeout
2. **Error caught** → Logged
3. **Fallback activated** → FallbackProvider generates response
4. **Execution continues** → No crash
5. **Database records** → Shows fallback was used

### Example

With Ollama running:
```
Provider: OllamaProvider
Model: neural-chat
Response: (from Ollama)
```

After stopping Ollama and retrying:
```
Provider: FallbackProvider  
Model: fallback
Response: (deterministic, same format)
```

**Same code path**, consistent behavior, graceful degradation!

## Performance Considerations

### Ollama Latency (Typical on GPU)
- **First run**: 1-3 seconds (model load)
- **Subsequent runs**: 200-500ms
- **On CPU**: 2-5 seconds per request

### Optimization Tips
1. Keep Ollama running (don't restart)
2. Use smaller model if latency is issue
3. Monitor `agent_executions.latency_ms` in DB
4. Consider quantization levels if available

## Troubleshooting

### "Ollama connection refused"

```bash
# Check if Ollama is running
ollama list

# If nothing, start it
ollama serve

# From backend container, test connectivity
curl http://host.docker.internal:11434/api/tags
```

### "Model not found: neural-chat"

```bash
# Pull the model
ollama pull neural-chat

# List available models
ollama list
```

### "JSON parsing error" from Ollama response

```bash
# Check Ollama is returning valid JSON
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "neural-chat", "prompt": "Say hello"}' | jq .
```

### To debug, check backend logs:

```bash
docker-compose logs backend | grep -i ollama
```

### Still having issues?

1. Try fallback mode: `LLM_PROVIDER=fallback`
2. Verify DB connectivity
3. Check Docker network: `docker network inspect resolveiq_default`

## Architecture Details

### OllamaProvider Implementation

Location: `backend/app/ai/llm/providers/ollama_provider.py`

**Key Methods:**

```python
generate(prompt, max_tokens, temperature)
  → POST /api/generate
  → Returns LLMResponse

generate_structured(prompt, schema, max_tokens, temperature)
  → POST /api/generate with format=json
  → Returns StructuredLLMResponse (validated)

embed(text)
  → POST /api/embeddings
  → Returns EmbeddingResponse

health_check()
  → GET /api/tags
  → Returns reachability + latency
```

**Structured Output Strategy:**

1. Append schema to prompt
2. Set `format: "json"` in Ollama API
3. Parse JSON from response
4. Validate against Pydantic schema
5. Raise if validation fails
6. Log parsing issues for debugging

### Prompt System

Location: `backend/app/ai/prompts.py`

Centralized prompts for all agents:

```python
PromptTemplates.UNDERSTANDING.analyze_complaint(text)
PromptTemplates.RESOLUTION.generate_resolution(text, category, ...)
PromptTemplates.SUPERVISOR.decide_routing(text, category, ...)
```

**Benefits:**
- Easy to tune prompts
- Consistent across providers
- Version control friendly
- No hard-coded prompts in agents

## Integration With Other Components

### Agents (Unchanged)

```python
# UnderstandingAgent
llm = get_llm_client()
await llm.generate_structured(prompt, ComplaintUnderstanding)

# ResolutionAgent
llm = get_llm_client()
await llm.generate_structured(prompt, ResolutionRecommendation)

# SupervisorAgent
llm = get_llm_client()
await llm.generate_structured(prompt, SupervisorDecision)
```

All three agents use identical interface - provider-agnostic!

### Future Extensions

**Embeddings (Phase 3):**

```python
llm = get_llm_client()
embedding = await llm.embed("Customer complaint text")
# Store in pgvector for RAG
```

**Token Counting:**

Currently Ollama doesn't expose token counts in API. This can be added if needed:

```python
# Future enhancement for cost tracking
response.tokens_used  # None for Ollama, set for OpenAI
```

## Testing

### Unit Tests

```bash
cd backend
pytest tests/test_llm_providers.py -v

# Run only Ollama tests
pytest tests/test_llm_providers.py::TestOllamaProvider -v

# Run only fallback tests
pytest tests/test_llm_providers.py::TestFallbackProvider -v
```

### Integration Tests (requires running Ollama)

```bash
export OLLAMA_TEST=true
pytest tests/test_llm_providers.py::TestOllamaProvider -v -m integration
```

## Demo Script

Quick test script:

```python
# tests/demo_ollama.py
import asyncio
from app.ai.llm.client import get_llm_client
from app.ai.models import ComplaintUnderstanding

async def demo():
    llm = get_llm_client()
    status = await llm.health_check()
    print(f"LLM Status: {status}")
    
    # If Ollama available, test it
    if status.get("reachable"):
        print("✓ Ollama is working!")
    else:
        print("✗ Ollama unavailable, using fallback")

asyncio.run(demo())
```

Run it:
```bash
python tests/demo_ollama.py
```

## Switching Providers

At runtime (if services restart):

```bash
# Use Ollama (default)
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434

# Use Demo mode (no external services)
export LLM_PROVIDER=fallback
export AI_MODE=demo

# Use OpenAI (if API key available)
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

Restart backend:
```bash
docker-compose restart backend
```

## Production Considerations

### For Production Deployment

1. **Use managed Ollama** or cloud LLM service
2. **Load balancing** - Multiple Ollama instances behind LB
3. **Caching** - Cache frequent prompts
4. **Rate limiting** - Prevent LLM API exhaustion
5. **Monitoring** - Track latencies and failures
6. **Fallbacks** - Always have backup provider

### Migration Path

```
Development: Ollama (local, free)
    ↓
Staging: Ollama or cloud LLM
    ↓
Production: Cloud LLM (OpenAI, Claude, etc) with Ollama fallback
```

The abstraction supports this seamlessly!

## Hackathon Tips

1. **Keep Ollama running** - Don't stop it if you restart containers
2. **Monitor latency** - Check `/api/v1/system/llm-status` frequently
3. **Test fallback** - Stop Ollama to demo graceful degradation
4. **Show status** - Frontend shows "Ollama Online" or "Using Fallback"
5. **Have backup plan** - If Ollama crashes, system keeps working

## Support & References

- **Ollama Docs**: https://ollama.ai
- **models.ollama.ai**: Available models to pull
- **Ollama API**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **ResolveIQ Architecture**: See docs/PHASE2_AGENTS.md

---

**Ollama is production-ready for local development and hackathons!** 🚀
