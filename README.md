# ResolveIQ

**Multi-Agent Customer Complaint Intelligence & Resolution Platform**

ResolveIQ transforms fragmented customer complaints into actionable intelligence through a sophisticated multi-agent system. Instead of simply closing tickets, ResolveIQ learns from complaints to identify operational patterns and prevent future issues.

ResolveIQ is a multi-agent customer complaint intelligence and resolution platform that unifies customer interactions, understands complaints, prioritizes them using business rules, investigates related issues, detects potential operational incidents, retrieves enterprise policy evidence, recommends grounded resolutions, and routes actions through controlled autonomy.

Phase 4 adds explainable complaint clustering and potential incident detection. See [Incident Intelligence](docs/INCIDENT_INTELLIGENCE.md) for scoring, thresholds, anomaly logic, lifecycle, and scaling notes.

## 🎯 Vision

Complaints → Understand → Prioritize → Investigate → Reason → Resolve → Learn

## How a complaint travels through ResolveIQ

The workflow orchestrator persists a compact complaint state and advances it through `CAPTURE`, `UNIFY`, `UNDERSTAND`, `PRIORITIZE`, `INVESTIGATE`, `REASON`, `SUPERVISOR`, `RESOLVE`, and `LEARN`. Existing agents handle interpretation and recommendation; deterministic tools handle customer history, priority, incident intelligence, policy retrieval, and business actions. Supervisor guardrails route each complaint to auto-resolution, human approval, or escalation. Approval pauses the checkpoint and resumes only the remaining graph, while every node produces an auditable ARC and workflow event.

## 🚀 Key Differentiators

1. **Multi-Agent Orchestration**: Specialized agents for intake, analysis, investigation, prioritization, and resolution
2. **Complaint-to-Incident Intelligence**: Detects when multiple complaints signal a broader operational issue
3. **RAG-Grounded Recommendations**: All suggestions are grounded in company policies and knowledge
4. **ARC Lifecycle Tracking**: Every complaint flows through CAPTURE → UNIFY → UNDERSTAND → PRIORITIZE → INVESTIGATE → REASON → RESOLVE → LEARN
5. **Human-in-the-Loop**: Approval center for review and escalation decision making
6. **Enterprise-Ready Architecture**: Modular, extensible, audit-trail enabled

## 📋 Problem Statement

Traditional support systems:
- Treat each complaint in isolation
- Rely on manual triage and routing
- Have no mechanism to detect operational incidents
- Don't learn from complaint patterns
- Can't correlate complaints across channels

**ResolveIQ solves this** by intelligently connecting dots between complaints to reveal systemic issues.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript + Vite)                       │
│  - Dashboard with real-time metrics                          │
│  - Complaint queue and detail views                          │
│  - ARC timeline visualization                                │
│  - Incident intelligence center                              │
│  - Approval workflow interface                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BACKEND API (FastAPI + Python)                             │
│  - Complaint lifecycle management                            │
│  - Agent orchestration layer                                 │
│  - Dashboard metrics aggregation                             │
│  - Workflow routing                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  AGENT LAYER                                                │
│  - Intake Agent: Normalize incoming complaints              │
│  - Classification Agent: Analyze & categorize               │
│  - Context Agent: Retrieve customer & order data            │
│  - Investigation Agent: Find related complaints             │
│  - Incident Detection: Identify operational patterns         │
│  - Policy Agent: RAG-based policy grounding                 │
│  - Resolution Agent: Generate actionable recommendations     │
│  - Supervisor Agent: Route decisions (auto/approval/escalate)│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PostgreSQL (Relational)                              │  │
│  │ - Customers, Orders, Complaints                      │  │
│  │ - Analysis, Priority, ARC Events                     │  │
│  │ - Incidents, Knowledge Documents                     │  │
│  │ - Audit Logs                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Vector Store (pgvector/Chroma)                       │  │
│  │ - Knowledge chunk embeddings                         │  │
│  │ - Complaint similarity search                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Redis                                                │  │
│  │ - Caching, Job queues                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Tech Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **Recharts** - Charting
- **Lucide React** - Icons

### Backend
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **PostgreSQL** - Primary database
- **pgvector** - Vector embeddings
- **Alembic** - Database migrations

### AI/Agents
- **OpenAI GPT** - LLM for intelligent analysis (configurable)
- **LLM Abstraction** - Provider-agnostic interface with fallback
- **Structured Outputs** - Pydantic-validated agent responses

## 🧠 Phase 1 vs Phase 2

### Phase 1: Foundation (✅ Complete)
- Complaint intake and lifecycle management
- Customer and order tracking
- Manual prioritization logic
- Dashboard with basic metrics
- ARC timeline visualization
- Docker deployment

### Phase 2: Real AI Intelligence (🚀 In Progress)
- **UnderstandingAgent** - LLM-powered complaint analysis
  - Sentiment analysis & classification
  - Entity extraction (product, order, location, etc)
  - Subcategory detection
  
- **ResolutionAgent** - AI-generated recommendations
  - Context-aware resolution suggestions
  - Considers customer tier & history
  - Compensation recommendations with reasoning
  
- **SupervisorAgent** - Intelligent routing with guardrails
  - Deterministic guardrails (legal, safety, high compensation)
  - LLM-based nuanced routing decisions
  - Routes to: AUTO_RESOLVE | HUMAN_APPROVAL | ESCALATE
  
- **Agent Execution Tracking** - Full observability
  - All agent operations logged with latency
  - Token usage tracking
  - Demo mode indicator
  
- **Demo Mode** - Works without API keys
  - Fallback provider for testing
  - Same code path as production
  - Graceful degradation

### Phase 2.5: Ollama Integration (✅ Complete)
- **Ollama as default provider** for development & hackathons
  - Local LLM - no external API keys needed
  - Fast iteration and testing
  - Gracefully falls back to demo mode if unavailable
- **Provider abstraction** - Seamless provider switching
  - Ollama (default local)
  - OpenAI (cloud)
  - Fallback (demo/testing)
- **Centralized prompts** - Easy to tune agent behavior
- **Health check endpoints** - Monitor LLM status
- **Full Docker support** - Pre-configured settings

## 🏃 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Run with Docker Compose

```bash
# Clone and navigate to project
cd resolveiq

# Copy environment template
cp .env.example .env

# Start all services
docker-compose up -d

# Initialize database and seed data
docker-compose exec backend python scripts/seed_db.py

# Access the application
Frontend:  http://localhost:5173
Backend:   http://localhost:8000
API Docs:  http://localhost:8000/docs
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp ../.env.example .env

# Start PostgreSQL and Redis, or set DATABASE_URL to a local test database.
# Copy the environment template from the repository root.

# Run database migrations from backend/
alembic upgrade head

# Seed demo data from backend/
python ../scripts/seed_db.py

# Start server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Local Demo Sharing with Cloudflare Quick Tunnel

This setup keeps the backend, database, agents, and Ollama on the local Windows PC. Vite serves the frontend publicly through a Cloudflare Quick Tunnel and proxies `/api` requests to the local FastAPI server; port 8000 is not exposed directly.

Open three PowerShell terminals from `C:\Users\conta\projects\resolveIQ`.

#### 1. Start the backend

```powershell
Set-Location C:\Users\conta\projects\resolveIQ
& .\.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "sqlite:///C:/Users/conta/projects/resolveIQ/resolveiq_demo.db"
$env:PYTHONPATH = "backend"
$env:AI_MODE = "demo"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

#### 2. Start the frontend

```powershell
Set-Location C:\Users\conta\projects\resolveIQ\frontend
npm run dev
```

Vite listens on `http://localhost:5173` and `http://0.0.0.0:5173` and proxies `/api/*` to `http://127.0.0.1:8000`.

#### 3. Start the Cloudflare Quick Tunnel

Install `cloudflared` first if it is not already available, then run:

```powershell
Set-Location C:\Users\conta\projects\resolveIQ
cloudflared tunnel --url http://localhost:5173
```

Cloudflare prints a public URL like `https://random-words.trycloudflare.com`. Share that URL with your teammate. Keep all three terminals running.

#### Troubleshooting

- **Public URL API calls fail:** Confirm the backend is responding at `http://127.0.0.1:8000/health`, the frontend is on port 5173, and the Vite terminal shows proxy requests.
- **Tunnel does not start:** Confirm `cloudflared --version`, install or update `cloudflared`, and check that another process is not already using the tunnel command.
- **Frontend still calls `localhost:8000`:** Remove any `VITE_API_URL` environment variable that points there, restart Vite, and verify browser requests use `/api/v1/...`.
- **Ollama does not respond:** Confirm Ollama is running locally and that the configured model is available. The documented `AI_MODE=demo` flow does not require Ollama.
- **Windows Firewall or network issues:** Allow `cloudflared.exe` and the local Vite process when Windows prompts. Do not open or port-forward 8000; the tunnel only needs access to local port 5173.

### Verify the system

From the repository root, run `pytest`. This executes the unit and complete
workflow integration tests with demo AI mode. Then start the backend and verify
`GET /health` and `GET /api/v1/system/llm-status`, followed by the frontend at
`http://localhost:5173`. Use Dashboard -> Run Demo to create or reuse the stable
demo complaint and inspect its complaint detail and ARC events.

See [docs/VALIDATION.md](docs/VALIDATION.md) for the complete validation matrix
and known limitations.

### Phase 3: Policy Grounding

RAG supplies fictional internal policy evidence to the ResolutionAgent; it does
not replace the LLM. Configure the embedding provider independently from the
chat model:

```bash
export EMBEDDING_PROVIDER=ollama
export EMBEDDING_MODEL=nomic-embed-text
```

Create and ingest a knowledge document through the internal API, then search it:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/documents \
  -H "Content-Type: application/json" \
  -d '{"title":"Delivery Policy","content":"Orders more than two business days late qualify for a delivery fee waiver.","document_type":"policy","category":"delivery"}'
curl -X POST http://localhost:8000/api/v1/knowledge/documents/{id}/ingest
curl "http://localhost:8000/api/v1/knowledge/search?q=late%20delivery"
```

The seeded policies are chunked, embedded, and searchable. Resolution responses
include concise policy evidence, source names, relevance scores, and grounding
confidence. If no evidence is available, the recommendation is marked for
human review rather than making an unsupported company-policy claim.

### Phase 2: AI Setup

#### Enable Real AI (OpenAI)

```bash
# Set OpenAI configuration
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-your-key-here
export LLM_MODEL=gpt-4-turbo

# Restart backend
docker-compose restart backend
# OR locally: uvicorn app.main:app --reload
```

#### Demo Mode (No API Key Required)

```bash
# Default configuration - uses fallback provider
export LLM_PROVIDER=fallback

# System works identically to real AI, but with deterministic outputs
# Useful for testing, demos, and development
```

#### Verify Agent Operations

```bash
# Check agent execution logs
SELECT 
    agent_name,
    COUNT(*) as total,
    AVG(latency_ms) as avg_ms,
    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failures
FROM agent_executions
GROUP BY agent_name;

# Monitor token usage
SELECT 
    DATE(started_at) as date,
    SUM(tokens_used) as total_tokens,
    COUNT(*) as total_calls
FROM agent_executions
WHERE model_used = 'gpt-4-turbo'
GROUP BY DATE(started_at);
```

## 📊 Demo Walkthrough

### Scenario: Customer Submits Late Delivery Complaint

1. **Complaint Submitted** → Frontend captures via web form
2. **CAPTURE** → System records complaint with metadata
3. **UNIFY** → Identifies customer and links to previous interactions
4. **UNDERSTAND** → UnderstandingAgent analyzes sentiment, extracts entities, categorizes
5. **PRIORITIZE** → Calculates priority score based on analysis
6. **INVESTIGATE** → Finds 8 similar complaints from last 2 days
7. **INCIDENT DETECTED** → "Potential Logistics Incident" with 85% confidence
8. **REASON** → ResolutionAgent suggests $20 refund + $20 credit with reasoning
9. **SUPERVISOR** → SupervisorAgent routes to auto-resolve (low risk)
10. **RESOLVE** → Complaint marked resolved, customer notified
11. **LEARN** → Incident added to dashboard, trend detected, alert sent to ops


**All visible in real-time on dashboard with ARC timeline!**

## 📊 Dashboard Metrics

- Total Complaints
- Open Complaints
- High Priority Complaints  
- Auto-Resolution Rate
- Average Resolution Time
- SLA Breach Rate
- Active Incidents
- Complaint Trends (7/30 days)
- Category Distribution
- Severity Distribution
- Channel Distribution

## 🗂️ Database Schema

### Core Entities
- **Customer**: Profile, tier, history
- **Order**: Product, shipping, status
- **Complaint**: Raw text, channel, status
- **ComplaintAnalysis**: Classification, sentiment, entities
- **ComplaintPriority**: Score, level, factors
- **ComplaintEvent**: ARC stage tracking
- **Incident**: Grouped related complaints
- **KnowledgeDocument**: Policy/FAQ storage
- **KnowledgeChunk**: Chunked docs for RAG
- **AuditLog**: Complete action history

## 🔄 Complaint Lifecycle

```
RECEIVED
  ↓
NORMALIZED
  ↓
CLASSIFIED
  ↓
PRIORITIZED
  ↓
INVESTIGATING
  ↓
RESOLUTION_PROPOSED
  ↓
PENDING_APPROVAL
  ↓  (approve)      (reject)        (escalate)
APPROVED    →    REJECTED         ESCALATED
  ↓
RESOLVED
  ↓
CLOSED
```

## 🧠 Agent Architecture

### 1. Intake Agent
- Normalizes complaints from any channel
- Extracts basic metadata (email, order ID, etc.)
- Detects language

### 2. Classification Agent  
- Categorizes complaint (delivery, billing, quality, etc.)
- Extracts entities (product, location, amount)
- Analyzes sentiment and urgency

### 3. Customer Context Agent
- Retrieves customer profile and tier
- Fetches recent order history
- Finds previous complaints
- Checks account status

### 4. Investigation Agent
- Finds similar complaints (semantic similarity)
- Detects related tickets
- Checks for duplicate complaints
- Identifies unusual patterns

### 5. Incident Intelligence
- Groups related complaints into potential incidents
- Calculates confidence scores
- Identifies affected regions/products
- Hypothesizes root causes

### 6. Policy Agent (RAG)
- Retrieves relevant company policies
- Searches knowledge base using semantic similarity
- Cites policy sources for recommendations
- Validates against guidelines

### 7. Resolution Agent
- Generates actionable recommendations
- Calculates appropriate compensation
- Proposes customer message
- Provides reasoning

### 8. Supervisor Agent
- Applies deterministic guardrails
- Routes to AUTO_RESOLVE, HUMAN_APPROVAL, or ESCALATE
- Enforces compensation limits
- Flags legal/safety issues

## 🔐 Security & Safety

- Environment-based configuration
- No API keys in code
- Input validation (Pydantic)
- Output schema validation
- Structured error handling
- Comprehensive audit logging
- Rate limiting ready
- Authorization-ready architecture

## 📝 API Endpoints

### Complaints
```
POST   /api/v1/complaints              - Create complaint
GET    /api/v1/complaints              - List complaints
GET    /api/v1/complaints/{id}         - Get detail
POST   /api/v1/complaints/{id}/analyze - Analyze
POST   /api/v1/complaints/{id}/prioritize - Prioritize
POST   /api/v1/complaints/{id}/investigate - Investigate  
POST   /api/v1/complaints/{id}/resolve - Generate resolution
POST   /api/v1/complaints/{id}/approve - Approve
POST   /api/v1/complaints/{id}/escalate - Escalate
```

### Dashboard
```
GET    /api/v1/dashboard/summary       - Summary metrics
GET    /api/v1/dashboard/trends        - Complaint trends
GET    /api/v1/dashboard/categories    - Category distribution
GET    /api/v1/dashboard/severity-distribution - Severity chart
GET    /api/v1/dashboard/channel-distribution - Channel chart
```

### Incidents
```
GET    /api/v1/incidents               - List incidents
GET    /api/v1/incidents/{id}          - Get detail
GET    /api/v1/incidents/{id}/complaints - Get linked complaints
```

### Customers
```
GET    /api/v1/customers               - List customers
GET    /api/v1/customers/{id}          - Get detail
GET    /api/v1/customers/{id}/complaints - Get complaints
GET    /api/v1/customers/{id}/orders   - Get orders
```

## 🔬 Testing

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests  
cd frontend
npm run test
```

## 📚 Project Structure

```
resolveiq/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/          # API handlers
│   │   ├── agents/                 # Agent implementations
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging.py
│   │   ├── domain/                 # Business logic (future)
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── rag/                    # RAG pipeline
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business services
│   │   ├── workflows/              # Orchestration (future)
│   │   └── main.py                 # FastAPI app
│   ├── alembic/                    # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable components
│   │   ├── pages/                  # Page components
│   │   ├── lib/
│   │   │   └── api.ts              # API client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── scripts/
│   └── seed_db.py                  # Demo data seeding
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

## 🚀 Deployment

### Docker Compose (Recommended for Hackathon)
```bash
docker-compose up -d
```

### Production Checklist
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Enable query logging/monitoring
- [ ] Configure rate limiting
- [ ] Set up alerting
- [ ] Test disaster recovery

## 🧪 Demo Data

Includes:
- 10 customers (various tiers)
- 60+ orders (mixed statuses)
- 50+ complaints (various categories and sentiments)
- 1 automatically detected incident (logistics)
- 5 knowledge documents (policies, FAQs)

Seed data with:
```bash
python scripts/seed_db.py
```

## 📖 Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Agent Design](docs/agent-design.md)
- [Data Model](docs/data-model.md)
- [RAG Implementation](docs/rag.md)
- [API Reference](docs/api.md)
- [Demo Walkthrough](docs/demo.md)

## 🔄 Development Phases

### ✅ Phase 1: Foundation (COMPLETE)
- [x] Docker setup
- [x] FastAPI backend
- [x] React frontend  
- [x] PostgreSQL schema
- [x] Database models
- [x] Basic API
- [x] Demo data seeding
- [x] Dashboard UI

### 🔄 Phase 2: Complaint Lifecycle (IN PROGRESS)
- [ ] Expand intake agent
- [ ] Implement classification pipeline
- [ ] Add priority calculation
- [ ] Build ARC event tracking
- [ ] Create SLA monitoring

### ⏳ Phase 3: RAG & Knowledge
- [ ] Implement vector stores
- [ ] Build RAG pipeline
- [ ] Create policy grounding
- [ ] Add retrieval evaluation

### ⏳ Phase 4: Advanced Agents
- [ ] LangGraph integration
- [ ] Multi-step reasoning
- [ ] Tool calling
- [ ] Structured outputs

### ⏳ Phase 5: Incident Intelligence
- [ ] Clustering algorithms
- [ ] Pattern detection
- [ ] Trend analysis
- [ ] Incident dashboard

### ⏳ Phase 6: Human-in-the-Loop
- [ ] Approval workflow UI
- [ ] Escalation routing
- [ ] Review tools
- [ ] Feedback loop

### ⏳ Phase 7: Polish & Deploy
- [ ] Performance optimization
- [ ] E2E testing
- [ ] Production readiness
- [ ] Documentation

## 🎯 Success Criteria

✅ **Hackathon MVP Checklist:**
- [x] End-to-end complaint workflow working
- [x] Multi-agent orchestration framework
- [x] Real-time ARC timeline
- [x] Dashboard with key metrics
- [x] Complaint-to-incident linking
- [x] Policy grounding mechanism
- [x] Human approval workflow
- [x] Audit trail
- [x] Demo data included
- [x] Docker deployment working
- [x] Professional UI
- [x] Comprehensive README

## 📞 Support

For questions or issues:
1. Check the [documentation](docs/)
2. Review [demo walkthrough](docs/demo.md)
3. Inspect database schema in [models](backend/app/models/)
4. Check API docs at `/docs` endpoint

## 📋 Known Limitations

- Agents currently mock LLM behavior (use actual LLM APIs in Phase 4)
- Single-node deployment (Kubernetes ready for scale)
- Basic incident clustering (ML-based in Phase 5)
- No authentication (ready architecture in place)

## 🚀 Future Enhancements

- LLM integration (OpenAI, Anthropic)
- Advanced NLP models
- Real-time streaming updates
- Mobile app
- Slack/Teams integration  
- Advanced analytics
- Predictive maintenance
- Customer journey mapping

## 📄 License

MIT

---

**Built with ❤️ for the Hackathon**

*ResolveIQ: Turning Complaints into Intelligence*
