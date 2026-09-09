"""Stateful complaint orchestration using the existing agents and services."""

import time
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models import (
    ARCStage, Complaint, ComplaintEvent, ComplaintStatus, WorkflowEvent, WorkflowRun,
)
from app.services.complaint_service import ComplaintService
from app.agents.critic_agent import CriticAgent
from app.services.decision_trace_service import DecisionTraceService
from app.core.config import settings
from app.rag.service import ensure_demo_policies
from .state import ComplaintWorkflowState


NODES = ("CAPTURE", "UNIFY", "UNDERSTAND", "PRIORITIZE", "INVESTIGATE", "REASON", "CRITIC", "SUPERVISOR", "RESOLVE", "LEARN")
ARC_FOR_NODE = {
    "CAPTURE": ARCStage.CAPTURE, "UNIFY": ARCStage.UNIFY,
    "UNDERSTAND": ARCStage.UNDERSTAND, "PRIORITIZE": ARCStage.PRIORITIZE,
    "INVESTIGATE": ARCStage.INVESTIGATE, "REASON": ARCStage.REASON, "CRITIC": ARCStage.REASON,
    "SUPERVISOR": ARCStage.RESOLVE, "RESOLVE": ARCStage.RESOLVE, "LEARN": ARCStage.LEARN,
}


class ComplaintGraph:
    """Small explicit graph with durable checkpoints and conditional routing."""

    def __init__(self, service: Optional[ComplaintService] = None):
        self.service = service or ComplaintService()
        self.critic = CriticAgent()
        self.trace = DecisionTraceService()

    async def run(self, db: Session, complaint_id: UUID, workflow_id: Optional[UUID] = None) -> WorkflowRun:
        complaint = await self.service.get_complaint(db, complaint_id)
        if not complaint:
            return None
        run = self._get_or_create_run(db, complaint, workflow_id)
        if run.status in {"completed", "cancelled", "pending_approval"}:
            return run
        await self._execute(db, run, complaint)
        return run

    async def resume(self, db: Session, workflow_id: UUID, approved: bool = True) -> WorkflowRun:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
        if not run:
            return None
        if run.status != "pending_approval":
            return run
        complaint = await self.service.get_complaint(db, run.complaint_id)
        if not complaint:
            return None
        run.state = {**(run.state or {}), "approval": {"approved": approved, "timestamp": datetime.utcnow().isoformat()}}
        if not approved:
            complaint.status = ComplaintStatus.ESCALATED
            run.current_node = "LEARN"
        else:
            complaint.status = ComplaintStatus.APPROVED
            run.current_node = "RESOLVE"
        run.status = "running"
        db.commit()
        if not approved:
            self._record_event(db, run, "RESOLVE", "ApprovalTool", {"decision": "rejected", "route": "ESCALATE"})
            run.current_node = "LEARN"
        await self._execute(db, run, complaint)
        return run

    async def retry(self, db: Session, workflow_id: UUID) -> WorkflowRun:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
        if not run:
            return None
        if run.status != "failed":
            return run
        run.retry_count = (run.retry_count or 0) + 1
        run.status = "running"
        run.last_error = None
        db.commit()
        complaint = await self.service.get_complaint(db, run.complaint_id)
        await self._execute(db, run, complaint)
        return run

    def _get_or_create_run(self, db: Session, complaint: Complaint, workflow_id: Optional[UUID]) -> WorkflowRun:
        if workflow_id:
            return db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
        active = db.query(WorkflowRun).filter(
            WorkflowRun.complaint_id == complaint.id,
            WorkflowRun.status.in_(["running", "pending_approval"]),
        ).first()
        if active:
            return active
        run = WorkflowRun(id=uuid4(), complaint_id=complaint.id, state={"complaint_id": str(complaint.id)})
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    async def _execute(self, db: Session, run: WorkflowRun, complaint: Complaint) -> None:
        start_index = NODES.index(run.current_node) if run.current_node in NODES else 0
        try:
            for node in NODES[start_index:]:
                if node == "SUPERVISOR" and run.state.get("supervisor_decision", {}).get("decision") == "HUMAN_APPROVAL":
                    run.status = "pending_approval"
                    run.current_node = "SUPERVISOR"
                    db.commit()
                    return
                node_started = time.perf_counter()
                output = await self._run_node(db, run, complaint, node)
                duration_ms = int((time.perf_counter() - node_started) * 1000)
                run.state = {**(run.state or {}), **output, "current_stage": node}
                run.current_node = node
                self._record_event(db, run, node, output.pop("agent_or_tool", "ComplaintGraph"), output, duration_ms)
                trace_result = output.get("decision") or output.get("action") or output.get("resolution_outcome") or output.get("overall_recommendation") or node.title()
                self.trace.record_event(db, str(complaint.id), node.title(), output.get("agent_or_tool", "ComplaintGraph"), str(trace_result), float(output.get("confidence") or 0))
                db.commit()
                if node == "SUPERVISOR" and output.get("decision") == "HUMAN_APPROVAL":
                    run.status = "pending_approval"
                    db.commit()
                    return
            run.status = "completed"
            run.current_node = "END"
            run.state = {**(run.state or {}), "workflow_status": "completed", "current_stage": "LEARN"}
            db.commit()
        except Exception as exc:
            run.status = "failed"
            run.last_error = str(exc)
            run.state = {**(run.state or {}), "errors": [*(run.state or {}).get("errors", []), str(exc)]}
            db.commit()
            raise

    async def _run_node(self, db: Session, run: WorkflowRun, complaint: Complaint, node: str) -> Dict[str, Any]:
        if node == "CAPTURE":
            return {"complaint": {"id": str(complaint.id), "channel": complaint.channel.value, "text": complaint.raw_text}, "agent_or_tool": "ComplaintCapture"}
        if node == "UNIFY":
            return {"customer_context": {"customer_id": str(complaint.customer_id), "tier": complaint.customer.tier, "email": complaint.customer.email}, "agent_or_tool": "CustomerContextTool"}
        if node == "UNDERSTAND":
            if not complaint.analysis:
                await self.service.analyze_complaint(db, complaint.id)
                db.refresh(complaint)
            analysis = complaint.analysis
            return {"understanding": {"category": analysis.category, "sentiment": str(analysis.sentiment), "severity": str(analysis.severity), "summary": analysis.summary}, "agent_or_tool": "UnderstandingAgent"}
        if node == "PRIORITIZE":
            if not complaint.priority:
                await self.service.prioritize_complaint(db, complaint.id)
                db.refresh(complaint)
            priority = complaint.priority
            return {"priority": {"score": priority.priority_score, "level": str(priority.priority_level), "reasons": priority.reasons or []}, "agent_or_tool": "PriorityEngine"}
        if node == "INVESTIGATE":
            result = await self.service.investigate_complaint(db, complaint.id)
            return {"investigation": result or {}, "related_complaints": (result or {}).get("related_ids", []), "agent_or_tool": "InvestigationTools"}
        if node == "REASON":
            if settings.ai_mode == "demo":
                await ensure_demo_policies(db)
            if not complaint.resolution_recommendation:
                await self.service.generate_resolution(db, complaint.id)
                db.refresh(complaint)
            recommendation = complaint.resolution_recommendation
            return {"resolution": {"action": recommendation.recommended_action, "confidence": recommendation.confidence, "requires_human_review": recommendation.requires_human_review, "policy_evidence": recommendation.policy_evidence or []}, "policy_evidence": recommendation.policy_evidence or [], "policy_evidence_available": bool(recommendation.policy_evidence), "agent_or_tool": "ResolutionAgent"}
        if node == "CRITIC":
            attempts = int((run.state or {}).get("critic_revision_attempts", 0))
            result = self.critic.evaluate(db, str(complaint.id))
            while result["overall_recommendation"] != "PASS" and attempts < 2:
                attempts += 1
                await self.service.generate_resolution(db, complaint.id)
                db.refresh(complaint)
                result = self.critic.evaluate(db, str(complaint.id))
            return {"critic": result, "critic_revision_attempts": attempts, "critic_passed": result["overall_recommendation"] == "PASS", "overall_recommendation": result["overall_recommendation"], "agent_or_tool": "CriticAgent"}
        if node == "SUPERVISOR":
            critic = (run.state or {}).get("critic", {})
            if critic and critic.get("overall_recommendation") != "PASS":
                return {"decision": "HUMAN_APPROVAL", "reasoning": "Critic validation requires structured human review before routing.", "confidence": 0.5, "risk_factors": ["Critic validation did not pass"], "agent_or_tool": "SupervisorGuardrail"}
            result = await self.service.supervisor_route_complaint(db, complaint.id)
            return {"supervisor_decision": result or {}, **(result or {}), "agent_or_tool": "SupervisorAgent"}
        if node == "RESOLVE":
            if complaint.status not in {ComplaintStatus.RESOLVED, ComplaintStatus.APPROVED}:
                complaint.status = ComplaintStatus.RESOLVED
                complaint.resolved_at = datetime.utcnow()
            return {"resolution_outcome": "resolved", "agent_or_tool": "MockEnterpriseAction"}
        if node == "LEARN":
            return {"learned": True, "agent_or_tool": "LearningAnalytics"}
        return {}

    def _record_event(self, db: Session, run: WorkflowRun, node: str, agent: str, output: Dict[str, Any], duration_ms: int) -> None:
        key = f"{run.id}:{node}"
        if db.query(WorkflowEvent).filter(WorkflowEvent.idempotency_key == key).first():
            return
        db.add(WorkflowEvent(workflow_id=run.id, complaint_id=run.complaint_id, node=node, arc_stage=ARC_FOR_NODE[node], agent_or_tool=agent, duration_ms=duration_ms, output_summary=self._compact(output), idempotency_key=key))
        if not db.query(ComplaintEvent).filter(ComplaintEvent.complaint_id == run.complaint_id, ComplaintEvent.arc_stage == ARC_FOR_NODE[node], ComplaintEvent.agent_name == agent).first():
            db.add(ComplaintEvent(complaint_id=run.complaint_id, arc_stage=ARC_FOR_NODE[node], agent_name=agent, status="completed", duration=duration_ms, output_reference=self._compact(output), timestamp=datetime.utcnow()))

    @staticmethod
    def _compact(value: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value[key] for key in value if key not in {"policy_evidence"} and key != "agent_or_tool"}