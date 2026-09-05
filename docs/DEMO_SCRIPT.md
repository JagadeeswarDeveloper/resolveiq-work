# ResolveIQ Hero Demo

Target duration: approximately three minutes in `AI_MODE=demo`.

| Time | Narration | Click / Expected result | Judge point |
|---|---|---|---|
| 0:00 | Complaints are signals, not isolated tickets. | Open Dashboard; show potential incident alert. | ResolveIQ connects support work to operations. |
| 0:20 | Submit the canonical late-delivery complaint. | Open Complaint Detail and click `Run orchestrator`. | One action starts a persisted workflow. |
| 0:40 | Understanding extracts frustration, category, and urgency. | Show UNDERSTAND and PRIORITIZE cards. | AI interprets; business rules score risk. |
| 1:00 | Investigation unifies customer history and related complaints. | Show INVESTIGATE and incident link. | Tools retrieve facts without LLM database access. |
| 1:20 | Policies ground the recommendation. | Show policy evidence excerpts. | Recommendations are defensible and source-backed. |
| 1:45 | The supervisor sees compensation and risk. | Show SUPERVISOR = HUMAN_APPROVAL. | Guardrails prevent unsafe autonomy. |
| 2:05 | A reviewer approves the controlled action. | Click `Approve and resolve`. | The checkpoint resumes at RESOLVE, not from the start. |
| 2:30 | The complaint resolves and learning is recorded. | Show RESOLVE, LEARN, completed status, and ARC. | Every transition is persisted and auditable. |
| 2:50 | The same graph supports different paths. | Optional: run FAQ and fraud fixtures. | Auto-resolve and escalation are deterministic alternatives. |

Launch locally:

```powershell
$env:DATABASE_URL = "sqlite:///./resolveiq_demo.db"
$env:AI_MODE = "demo"
$env:PYTHONPATH = "backend"
c:/Users/conta/projects/resolveIQ/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload
Push-Location frontend
npm run dev
Pop-Location
```
