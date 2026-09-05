# ResolveIQ Phase 2 - AI Agents Quick Start

## What's New

You now have **three AI agents** that intelligently handle customer complaints:

1. **UnderstandingAgent** - Analyzes and classifies complaints
2. **ResolutionAgent** - Generates personalized resolutions
3. **SupervisorAgent** - Routes complaints intelligently

## Enable AI Features

### Option 1: With Real AI (OpenAI)

```bash
# Set environment variables
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-your-openai-key
export LLM_MODEL=gpt-4-turbo

# Restart backend
docker-compose restart backend
```

### Option 2: Demo Mode (No API Key Needed)

```bash
# Set environment variable (or use default)
export LLM_PROVIDER=fallback

# Restart backend
docker-compose restart backend

# System works perfectly, just with deterministic outputs
# Great for testing and demos!
```

## Quick Test

### 1. Create a Complaint

```bash
curl -X POST http://localhost:8000/api/complaints \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "raw_text": "I ordered a laptop 2 weeks ago and it still hasnt arrived!",
    "customer_email": "customer@example.com"
  }'

# Copy the complaint ID from response
COMPLAINT_ID="..."
```

### 2. Analyze (UnderstandingAgent)

```bash
curl -X POST http://localhost:8000/api/complaints/$COMPLAINT_ID/analyze

# Response shows AI analysis:
# - Category: "delivery"
# - Sentiment: "FRUSTRATED" 
# - Entities extracted
# - Summary generated
```

### 3. Generate Resolution (ResolutionAgent)

```bash
curl -X POST http://localhost:8000/api/complaints/$COMPLAINT_ID/resolve

# Response shows AI recommendation:
# - Action: "Ship overnight replacement..."
# - Compensation: "$25 store credit"
# - Confidence: 0.88
```

### 4. Route Complaint (SupervisorAgent)

```bash
curl -X POST http://localhost:8000/api/complaints/$COMPLAINT_ID/route

# Response shows routing decision:
# - Decision: "AUTO_RESOLVE" (or HUMAN_APPROVAL / ESCALATE)
# - Confidence: 0.92
# - Guardrails applied: []
```

## How Agents Work Together

```
User submits complaint
    ↓
[UNDERSTAND] UnderstandingAgent analyzes
    - Sentiment, category, entities
    ↓
[PRIORITIZE] System calculates priority
    - Uses analysis results
    ↓
[INVESTIGATE] System finds related complaints
    ↓
[REASON] ResolutionAgent suggests solution
    - Considers customer context
    ↓
[RESOLVE] SupervisorAgent routes
    - Apply guardrails
    - Make routing decision
    ↓
Auto-resolve OR Send for human approval
```

## Agent Execution Tracking

Every agent operation is logged with:
- ✅ Agent name
- ✅ Latency (ms)
- ✅ Tokens used (if using real AI)
- ✅ Status (completed/failed)
- ✅ Demo mode indicator

Query execution logs:
```sql
SELECT 
    agent_name,
    COUNT(*) as runs,
    AVG(latency_ms) as avg_ms,
    SUM(tokens_used) as total_tokens
FROM agent_executions
GROUP BY agent_name;
```

## Error Handling

All agents have graceful error handling:

1. **LLM Error** → Automatically tries fallback provider
2. **Schema Error** → Logs and raises with context
3. **Database Error** → Transaction rolls back safely

Performance remains excellent even if OpenAI is down!

## Guardrails (SupervisorAgent)

Auto-ESCALATE if complaint mentions:
- Legal/lawsuit issues
- Safety/injury concerns
- Death/poison/recall
- Regulatory/compliance

Auto-SEND FOR APPROVAL if:
- Compensation exceeds $100 (configurable)
- Resolution agent flagged for review
- SLA breached on high-priority complaint

Otherwise:
- Let AI decide via LLM (nuanced routing)

## Configuration

### Compensation Threshold

```bash
# Set in environment or .env
COMPENSATION_THRESHOLD=100  # Dollar amount

# Adjust as needed for your business
```

### LLM Model

```bash
# Change model selection
LLM_MODEL=gpt-4-turbo        # Most capable
LLM_MODEL=gpt-4              # Faster, cheaper
LLM_MODEL=gpt-3.5-turbo      # Budget option
```

## Monitoring

### Check Agent Health

```bash
# See all agent operations
SELECT * FROM agent_executions 
ORDER BY started_at DESC 
LIMIT 20;

# See failures
SELECT * FROM agent_executions 
WHERE status = 'failed' 
ORDER BY started_at DESC;

# Performance by agent
SELECT agent_name,
       COUNT(*) as calls,
       AVG(latency_ms) as avg_latency,
       MAX(latency_ms) as max_latency
FROM agent_executions
GROUP BY agent_name;
```

### API Docs

Open http://localhost:8000/docs to see all endpoints:
- `/complaints` - Create/list complaints
- `/complaints/{id}/analyze` - Trigger UnderstandingAgent
- `/complaints/{id}/resolve` - Trigger ResolutionAgent
- `/complaints/{id}/route` - Trigger SupervisorAgent
- And more Phase 1 endpoints...

## Troubleshooting

### Agent not using AI, using demo mode?
Check LLM_PROVIDER and LLM_API_KEY are set correctly.

### Slow responses?
- Check network/API latency
- Monitor token usage
- Consider faster models

### Want deterministic outputs?
Set `LLM_PROVIDER=fallback` - perfect for testing!

### Need custom logic?
Edit agent files in `backend/app/agents/`:
- `understanding_agent.py`
- `resolution_agent.py`
- `supervisor_agent.py`

Each agent is well-documented and easy to modify.

## Examples

### Example 1: Late Delivery

```
Input: "My order arrived 3 weeks late!"

Understanding:
  - Category: delivery
  - Sentiment: FRUSTRATED (0.8)
  - Urgency: HIGH

Resolution:
  - Action: "Process $50 refund + $25 credit"
  - Compensation: $75 total
  - Confidence: 0.90

Supervisor:
  - Decision: AUTO_RESOLVE (low risk, high confidence)
```

### Example 2: Safety Concern

```
Input: "The phone I received is smoking and hot to touch!"

Understanding:
  - Category: product_quality
  - Sentiment: CRITICAL (0.95)
  - Urgency: CRITICAL

Resolution:
  - Action: "Immediate replacement + Safety investigation"
  - Requires: Human review

Supervisor:
  - Decision: ESCALATE (safety guardrail)
  - Reason: "Safety concern detected"
```

## Next Steps

1. ✅ Test agents with demo data
2. ✅ Review agent logs in database
3. ✅ Set OpenAI API key for real AI
4. ✅ Monitor performance metrics
5. ⚙️ Tune guardrails for your business
6. 🎯 Implement in production workflow

## Documentation

- Full architecture: [PHASE2_AGENTS.md](./PHASE2_AGENTS.md)
- API reference: http://localhost:8000/docs
- Agent code: `backend/app/agents/`
- Models: `backend/app/ai/models.py`

## Support

Check logs:
```bash
# Backend logs
docker-compose logs backend

# Database logs
docker-compose logs postgres
```

All agent operations are logged with full context for debugging!

---

**Your AI-powered complaint system is ready! 🚀**
