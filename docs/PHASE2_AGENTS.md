# ResolveIQ Phase 2: AI Agents Implementation

## Overview

Phase 2 adds three AI agents on top of the Phase 1 foundation. These agents transform the complaint handling system from deterministic to intelligently reasoned, while maintaining all existing functionality.

## Architecture

### Three-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLAINT LIFECYCLE                       │
└─────────────────────────────────────────────────────────────┘
        │
        ├─> [CAPTURE] Manual receipt (Phase 1)
        │
        ├─> [UNDERSTAND] UnderstandingAgent
        │   ├─ Analyzes raw complaint
        │   ├─ Classifies category & sentiment
        │   ├─ Extracts entities (product, order, location, etc)
        │   ├─ Returns: ComplaintAnalysis
        │   └─ Logs: AgentExecution
        │
        ├─> [PRIORITIZE] Priority logic (Phase 1)
        │   └─ Uses analysis results for scoring
        │
        ├─> [INVESTIGATE] Investigation logic (Phase 1)
        │   └─ Finds related complaints
        │
        ├─> [REASON] ResolutionAgent
        │   ├─ Generates resolution recommendation
        │   ├─ Considers customer context & tier
        │   ├─ Returns: ResolutionRecommendation
        │   └─ Logs: AgentExecution
        │
        ├─> [RESOLVE] SupervisorAgent
        │   ├─ Applies deterministic guardrails
        │   ├─ Routes complaint (AUTO_RESOLVE | HUMAN_APPROVAL | ESCALATE)
        │   ├─ Returns: SupervisorDecision
        │   └─ Logs: AgentExecution
        │
        └─> Auto-resolution OR Human review
```

### LLM Abstraction Layer

All agents use a unified `LLMClient` that:
- **Supports multiple providers** (OpenAI with fallback)
- **Graceful degradation** - works without API keys in demo mode
- **Structured outputs** - validates responses against Pydantic schemas
- **Async design** - non-blocking AI operations

```
LLMClient
  ├─ generate()              # Free-form text generation
  ├─ generate_structured()   # Structured output with schema validation
  └─ embed()                 # Embeddings (for future use)
      │
      ├─> OpenAIProvider (real LLM if API key available)
      │   ├─ JSON schema generation from Pydantic
      │   ├─ Async requests to OpenAI API
      │   └─ Error handling with fallback
      │
      └─> FallbackProvider (deterministic demo mode)
          ├─ Schema-aware output generation
          ├─ Same response structure as real LLM
          └─ No API calls = always works
```

## Database Models

### New Tables

#### `supervisor_decisions`
Routes complaint based on risk assessment:
- `decision`: AUTO_RESOLVE | HUMAN_APPROVAL | ESCALATE
- `confidence`: 0.0-1.0
- `guardrails_applied`: List of rules triggered
- `risk_factors`: List of identified risks

#### Modified `agent_executions`
Tracks all agent operations:
- `agent_name`: UnderstandingAgent | ResolutionAgent | SupervisorAgent
- `arc_stage`: Which lifecycle stage
- `status`: pending → in_progress → completed/failed
- `model_used`: Which LLM model
- `tokens_used`: API usage tracking
- `latency_ms`: Performance monitoring
- `is_demo_mode`: Indicates fallback provider was used

#### Modified `resolution_recommendations`
Stores agent-generated recommendations:
- Now populated by ResolutionAgent (not mock data)
- Contains reasoning and policy sources
- Tracks confidence and review requirements

## Agent Implementations

### 1. UnderstandingAgent

**Purpose**: Analyze raw complaint text and extract structured understanding.

**Input**:
```python
complaint.raw_text = "I ordered a laptop 2 weeks ago and it still hasn't arrived. 
                      I've been trying to contact support but no response!"
```

**Output** (ComplaintUnderstanding):
```python
{
    "category": "delivery",
    "subcategory": "late_delivery",
    "intent": "urgent_delivery_tracking",
    "sentiment": SentimentEnum.FRUSTRATED,
    "sentiment_score": 0.75,
    "urgency": "HIGH",
    "summary": "Customer reports delayed laptop delivery after 2 weeks with no support response",
    "entities": {
        "product": "laptop",
        "order_id": None,
        "location": None,
        "account_issue": "support_unresponsive",
        "payment": None
    }
}
```

**Database**: Creates/updates `complaints.analysis` record

**Guardrails**: None - pure analysis

**Error Handling**: Falls back to generic analysis if LLM fails

### 2. ResolutionAgent

**Purpose**: Generate actionable resolution recommendations considering customer context.

**Input**:
- Complaint text
- Category and sentiment (from UnderstandingAgent)
- Customer tier and lifetime value
- Historical complaint count
- Priority level

**Output** (ResolutionRecommendation):
```python
{
    "recommended_action": "Ship overnight replacement with tracking",
    "customer_response": "We sincerely apologize for the delayed delivery. 
                          We're sending a replacement via overnight shipping 
                          and providing $25 store credit for the inconvenience.",
    "internal_actions": [
        "Check warehouse inventory",
        "Flag shipping carrier for investigation",
        "Add customer to VIP support queue"
    ],
    "compensation": {
        "type": "store_credit",
        "amount": 25,
        "reason": "Delayed delivery + support unresponsiveness"
    },
    "confidence": 0.88,
    "requires_human_review": False
}
```

**Database**: Creates `resolution_recommendations` record

**Guardrails**: None - pure generation

**Error Handling**: Suggests manual review if generation fails

### 3. SupervisorAgent

**Purpose**: Route complaint with deterministic guardrails protecting customer satisfaction and risk.

**Guardrails** (Deterministic Rules):
1. **Legal/Safety Keywords** → ESCALATE
   - Triggers on: "legal", "lawsuit", "injury", "death", "recall", etc.
   
2. **High Compensation** → HUMAN_APPROVAL
   - Default threshold: $100
   - Configurable via `compensation_threshold` setting
   
3. **Agent-Flagged Review** → HUMAN_APPROVAL
   - If ResolutionAgent sets `requires_human_review=true`
   
4. **SLA Breach + High Priority** → HUMAN_APPROVAL
   - SLA breached on HIGH or CRITICAL priority
   
5. **Default** → LLM Decides
   - Calls LLM for nuanced routing if no guardrails triggered
   - LLM considers confidence, risk, customer impact

**Output** (SupervisorDecision):
```python
{
    "decision": SupervisorDecisionEnum.AUTO_RESOLVE,  # or HUMAN_APPROVAL, ESCALATE
    "reasoning": "Low-risk resolution, high confidence, satisfied customer likely",
    "confidence": 0.92,
    "guardrails_applied": [],  # Empty = LLM decided
    "risk_factors": [],
    "escalation_reason": None
}
```

**Status Transitions**:
- `AUTO_RESOLVE` → Complaint immediately set to RESOLVED
- `HUMAN_APPROVAL` → Complaint set to PENDING_APPROVAL (supervisor review)
- `ESCALATE` → Complaint set to ESCALATED (management review)

**Database**: Creates `supervisor_decisions` record

## API Endpoints

### Analyze Complaint
```
POST /api/complaints/{complaint_id}/analyze

Response:
{
    "success": true,
    "message": "Complaint analyzed",
    "data": {
        "category": "delivery",
        "sentiment": "negative",
        "sentiment_score": 0.75,
        "summary": "Late delivery complaint"
    }
}
```

### Generate Resolution
```
POST /api/complaints/{complaint_id}/resolve

Response:
{
    "success": true,
    "message": "Resolution generated",
    "data": {
        "recommended_action": "Ship replacement via overnight",
        "confidence": 0.88,
        "compensation": {"type": "credit", "amount": 25}
    }
}
```

### Route Complaint (Supervisor)
```
POST /api/complaints/{complaint_id}/route

Response:
{
    "success": true,
    "message": "Complaint routed",
    "data": {
        "decision": "AUTO_RESOLVE",
        "reasoning": "Low-risk, high confidence",
        "confidence": 0.92,
        "guardrails": []
    }
}
```

## Workflow Integration

### Complete Complaint Flow

```python
# 1. Create complaint (Phase 1)
await complaint_service.create_complaint(db, complaint_data)

# 2. Analyze with AI (Phase 2)
analysis = await complaint_service.analyze_complaint(db, complaint_id)
# → UnderstandingAgent processes complaint
# → Creates ComplaintAnalysis
# → Logs AgentExecution

# 3. Prioritize (Phase 1, uses analysis)
priority = await complaint_service.prioritize_complaint(db, complaint_id)
# → Uses sentiment & category from analysis
# → Calculates priority score

# 4. Investigate (Phase 1)
investigation = await complaint_service.investigate_complaint(db, complaint_id)
# → Finds related complaints

# 5. Generate resolution (Phase 2)
recommendation = await complaint_service.generate_resolution(db, complaint_id)
# → ResolutionAgent processes all context
# → Creates ResolutionRecommendation
# → Logs AgentExecution

# 6. Route with supervisor (Phase 2)
decision = await complaint_service.supervisor_route_complaint(db, complaint_id)
# → SupervisorAgent applies guardrails + LLM
# → Creates SupervisorDecision
# → Updates complaint status
# → Logs AgentExecution

# 7. Auto-resolve OR await human approval
# → If AUTO_RESOLVE: immediately marked RESOLVED
# → If HUMAN_APPROVAL: awaits supervisor.approve_complaint()
# → If ESCALATE: awaits manager.escalate_complaint()
```

## Demo Mode

When LLM API key is not available:

1. **FallbackProvider** generates deterministic outputs
2. All agents work identically to production
3. Responses are valid and schema-compliant
4. `AgentExecution.is_demo_mode=true` tracks this

**Benefits**:
- Demo/testing without API costs
- Same code path as production
- Easy integration testing
- Graceful degradation

## Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER=openai              # or 'fallback'
LLM_API_KEY=sk-...               # OpenAI API key
LLM_MODEL=gpt-4-turbo           # Model selection

# Supervisor Guardrails
COMPENSATION_THRESHOLD=100       # $ amount triggering human approval
```

### Settings (app/core/config.py)

```python
class Settings(BaseSettings):
    # LLM settings
    llm_provider: str = "openai"
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4-turbo"
    
    # Supervisor settings
    compensation_threshold: float = 100.0
```

## Testing

### Unit Tests

```bash
python -m pytest tests/test_agents.py -v
```

### Integration Test Script

```bash
python tests/test_agents.py
```

Output shows:
- LLM client initialization
- Prompt generation
- Guardrail detection
- Error handling

### Manual Testing in Docker

```bash
# Start services
docker-compose up -d

# Create complaint
curl -X POST http://localhost:8000/api/complaints \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "raw_text": "Order arrived late and damaged!",
    "customer_email": "test@example.com"
  }'

# Analyze
curl -X POST http://localhost:8000/api/complaints/{id}/analyze

# Generate resolution
curl -X POST http://localhost:8000/api/complaints/{id}/resolve

# Route with supervisor
curl -X POST http://localhost:8000/api/complaints/{id}/route
```

## Monitoring & Observability

### Agent Execution Tracking

All agent operations logged to `agent_executions` table:

```python
SELECT 
    agent_name,
    COUNT(*) as total_runs,
    AVG(latency_ms) as avg_latency,
    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failures,
    SUM(tokens_used) as total_tokens
FROM agent_executions
GROUP BY agent_name
```

### Performance Metrics

```python
# Average agent latency by agent
SELECT 
    agent_name,
    AVG(latency_ms) as avg_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_ms
FROM agent_executions
WHERE status = 'completed'
GROUP BY agent_name
```

### Demo Mode Usage

```python
# Track demo mode vs production
SELECT 
    is_demo_mode,
    COUNT(*) as usage_count,
    AVG(latency_ms) as avg_latency
FROM agent_executions
GROUP BY is_demo_mode
```

## Error Handling

Each agent has three-level error handling:

### Level 1: LLM Error
- LLM call fails
- FallbackProvider used automatically
- Logged but execution continues

### Level 2: Schema Validation Error
- LLM response doesn't match schema
- Pydantic raises validation error
- Agent catches, logs, raises with context

### Level 3: Database Error
- DB transaction fails
- AgentExecution's finally-block commits status=failed
- Service catches, returns error response
- Complaint status reverts to previous state

## Next Steps (Future Enhancements)

1. **Chain-of-thought logging** - Capture agent reasoning steps
2. **Feedback loop** - Learn from human corrections
3. **Fine-tuning** - Custom models for organization
4. **Batch processing** - Analyze complaints in batch queries
5. **Multi-language support** - Extend beyond English complaints
6. **Incident detection** - SupervisorAgent flags mass complaints
7. **Analytics dashboard** - Real-time agent performance metrics

## Files Structure

```
backend/app/
├── agents/
│   ├── __init__.py
│   ├── understanding_agent.py      # Complaint analysis
│   ├── resolution_agent.py         # Resolution generation
│   └── supervisor_agent.py         # Routing decisions
├── ai/
│   ├── __init__.py
│   ├── models.py                   # Pydantic schemas for AI outputs
│   └── llm/
│       ├── __init__.py
│       ├── base.py                 # Abstract LLMProvider
│       ├── client.py               # Unified LLMClient (singleton)
│       └── providers/
│           ├── __init__.py
│           ├── openai_provider.py  # Real OpenAI implementation
│           └── fallback_provider.py # Demo/fallback mode
├── models/
│   └── __init__.py                 # Added SupervisorDecision table
├── services/
│   └── complaint_service.py        # Updated with agent integration
└── api/endpoints/
    └── complaints.py               # Added /route endpoint
```

## Validation Checklist

- ✅ Three agents implemented with proper async/await
- ✅ LLM abstraction layer with fallback
- ✅ Database models for persistent tracking
- ✅ API endpoints for agent operations
- ✅ Error handling and logging
- ✅ Demo mode graceful degradation
- ✅ Agent execution tracking
- ✅ Supervisor guardrails (deterministic)
- ✅ Service integration complete
- ✅ Test script created

## Known Limitations

1. **Chain-of-thought**: Not stored, only final output
2. **Streamed responses**: Not supported, only final output
3. **Multi-modal**: Text-only, no images
4. **Real-time**: Batch operations not optimized
5. **Fine-tuning**: Uses base models only

These can be addressed in future phases.
