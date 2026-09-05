"""Workflow orchestration endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models import WorkflowEvent, WorkflowRun
from app.workflows import ComplaintGraph

router = APIRouter()
graph = ComplaintGraph()


def _payload(run: WorkflowRun) -> dict:
    return {
        "workflow_id": str(run.id), "complaint_id": str(run.complaint_id),
        "status": run.status, "current_node": run.current_node,
        "state": run.state or {}, "retry_count": run.retry_count or 0,
        "last_error": run.last_error,
    }


@router.post("/complaints/{complaint_id}/run")
async def run_workflow(complaint_id: UUID, db: Session = Depends(get_db)):
    run = await graph.run(db, complaint_id)
    if not run:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _payload(run)


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _payload(run)


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: UUID, approved: bool = True, db: Session = Depends(get_db)):
    run = await graph.resume(db, workflow_id, approved)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _payload(run)


@router.post("/{workflow_id}/retry")
async def retry_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    run = await graph.retry(db, workflow_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _payload(run)


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if run.status not in {"completed", "cancelled"}:
        run.status = "cancelled"
        db.commit()
    return _payload(run)


@router.get("/{workflow_id}/events")
async def workflow_events(workflow_id: UUID, db: Session = Depends(get_db)):
    if not db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first():
        raise HTTPException(status_code=404, detail="Workflow not found")
    events = db.query(WorkflowEvent).filter(WorkflowEvent.workflow_id == workflow_id).order_by(WorkflowEvent.timestamp).all()
    return [{"node": e.node, "arc_stage": e.arc_stage.value, "agent_or_tool": e.agent_or_tool, "status": e.status, "duration_ms": e.duration_ms, "output_summary": e.output_summary, "error": e.error, "timestamp": e.timestamp} for e in events]