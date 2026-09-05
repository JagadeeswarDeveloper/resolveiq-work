# ResolveIQ Validation

## Required checks

Run from the repository root unless noted:

```powershell
.\.venv\Scripts\python.exe -m pytest
Push-Location frontend; npm run build; Pop-Location
Push-Location backend; $env:DATABASE_URL='sqlite:///./validation.db'; .\..\.venv\Scripts\python.exe -m alembic upgrade head; .\..\.venv\Scripts\python.exe ..\scripts\seed_db.py; Pop-Location
```

For an API smoke test, run the migration before starting the application or
creating requests against a new database:

```powershell
Push-Location backend
$env:PYTHONPATH='.'
$env:DATABASE_URL='sqlite:///./validation.db'
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; client=TestClient(app); client.__enter__(); print('health', client.get('/health').status_code); print('llm', client.get('/api/v1/system/llm-status').status_code); print('demo', client.post('/api/v1/complaints/demo').status_code); client.__exit__(None, None, None)"
Pop-Location
```

The normal suite uses demo AI mode and a disposable SQLite database. The optional Ollama integration test is enabled with `OLLAMA_TEST=true`; it fails clearly when Ollama or its configured model is unavailable.

## Current validation

- Backend tests: 28 passed; the optional Ollama test is skipped unless `OLLAMA_TEST=true`.
- Frontend TypeScript and Vite build: passed; Vite reports only a bundle-size warning.
- Alembic clean upgrade: passed on SQLite.
- Seed script: passed on SQLite, creating customers, orders, complaints, an incident, analysis/priority data, and knowledge documents.
- API smoke and complete workflow: passed after clean migration; Run Demo returns the stable complaint with persisted ARC events.
- RAG ingestion, retrieval, grounding, and missing-evidence supervisor tests: passed.
- Knowledge API document listing, search, and health smoke checks: passed.
- Docker Compose: not executable in the audit environment because Docker was unavailable.

## Known limitations

- PostgreSQL and Docker runtime validation still requires the target environment.
- The fallback provider is used for deterministic tests; live Ollama requires the configured model to be installed.
- Ollama chat availability does not guarantee the configured embedding endpoint/model is available; RAG falls back to deterministic local embeddings and records the configured embedding settings.
- Approval is currently represented by the existing complaint detail actions; the approval route is a minimal queue landing page.
