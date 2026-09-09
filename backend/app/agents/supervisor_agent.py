"""Supervisor Agent - makes routing decisions with deterministic guardrails."""

import logging
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    Complaint, ComplaintAnalysis, ComplaintPriority, ResolutionRecommendation,
    AgentExecution, ARCStage, PriorityLevel
)
from app.ai.llm.client import get_llm_client
from app.ai.models import SupervisorDecision, SupervisorDecisionEnum
from app.ai.prompts import PromptTemplates
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Supervisor agent - determines complaint routing with guardrails."""

    def __init__(self):
        self.llm = get_llm_client()
        self.agent_name = "SupervisorAgent"
        
        # Configuration for guardrails
        self.compensation_threshold = getattr(settings, "compensation_threshold", 100.0)
        self.escalation_keywords = [
            "legal", "fraud", "criminal", "lawsuit", "safety",
            "regulatory", "compliance", "dangerous", "injury",
            "death", "poison", "recall", "account takeover",
            "unauthorized", "unrecognized payment", "changed my email",
            "changed the email", "payment method"
        ]

    async def decide_routing(
        self,
        db: Session,
        complaint: Complaint,
    ) -> SupervisorDecision:
        """Decide how to route complaint (auto-resolve, approval, escalate)."""
        
        execution_start = time.time()
        execution = AgentExecution(
            complaint_id=complaint.id,
            agent_name=self.agent_name,
            arc_stage=ARCStage.RESOLVE,
            status="in_progress",
            started_at=datetime.utcnow(),
            is_demo_mode=self.llm.is_demo_mode(),
        )
        
        try:
            # Apply deterministic guardrails first
            guardrail_decision = self._apply_guardrails(complaint, db)
            if guardrail_decision:
                logger.info(f"Supervisor applying guardrail: {guardrail_decision.decision}")
                decision = guardrail_decision
            else:
                # No guardrails triggered, consult LLM for nuanced decision
                logger.info(f"Supervisor consulting LLM for routing decision")
                decision = await self._llm_decide(complaint, db)
            
            # Record successful execution
            latency_ms = int((time.time() - execution_start) * 1000)
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = latency_ms
            execution.output_summary = {
                "decision": decision.decision,
                "confidence": decision.confidence,
                "guardrails": decision.guardrails_applied,
            }
            
            logger.info(f"Supervisor decision: {decision.decision} (confidence: {decision.confidence})")
            
        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            latency_ms = int((time.time() - execution_start) * 1000)
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = latency_ms
            execution.error_message = str(e)
            raise
        
        finally:
            db.add(execution)
            db.commit()
        
        return decision

    def _apply_guardrails(
        self,
        complaint: Complaint,
        db: Session,
    ) -> Optional[SupervisorDecision]:
        """Apply deterministic business rule guardrails."""
        
        guardrails_applied = []
        risk_factors = []
        
        # Check complaint text for keywords
        complaint_text_lower = complaint.raw_text.lower()
        
        # ESCALATION: Legal/safety/regulatory issues
        for keyword in self.escalation_keywords:
            if keyword in complaint_text_lower:
                risk_factors.append(f"Contains keyword: {keyword}")
                return SupervisorDecision(
                    decision=SupervisorDecisionEnum.ESCALATE,
                    reasoning="Legal, safety, or regulatory concern detected",
                    confidence=0.95,
                    guardrails_applied=["legal_safety_escalation"],
                    escalation_reason=f"Keyword detected: {keyword}",
                    risk_factors=risk_factors,
                )
        
        # Check resolution recommendation if available
        recommendation = db.query(ResolutionRecommendation).filter(
            ResolutionRecommendation.complaint_id == complaint.id
        ).first()

        if recommendation and not recommendation.policy_evidence:
            return SupervisorDecision(
                decision=SupervisorDecisionEnum.HUMAN_APPROVAL,
                reasoning="No policy evidence supports the proposed resolution",
                confidence=0.95,
                guardrails_applied=["missing_policy_evidence"],
                risk_factors=["Ungrounded resolution recommendation"],
            )
        
        if recommendation:
            # ESCALATION: Requires human review
            if recommendation.requires_human_review:
                guardrails_applied.append("requires_human_review")
                return SupervisorDecision(
                    decision=SupervisorDecisionEnum.HUMAN_APPROVAL,
                    reasoning="Resolution agent flagged for human review",
                    confidence=0.9,
                    guardrails_applied=guardrails_applied,
                    risk_factors=risk_factors,
                )
            
            # ESCALATION: High compensation exceeds threshold
            if recommendation.compensation:
                comp_amount = recommendation.compensation.get("amount", 0) or 0
                if comp_amount > self.compensation_threshold:
                    guardrails_applied.append("high_compensation")
                    risk_factors.append(f"Compensation ${comp_amount} exceeds threshold ${self.compensation_threshold}")
                    return SupervisorDecision(
                        decision=SupervisorDecisionEnum.HUMAN_APPROVAL,
                        reasoning=f"Compensation ${comp_amount} requires approval",
                        confidence=0.9,
                        guardrails_applied=guardrails_applied,
                        risk_factors=risk_factors,
                    )
        
        # Check priority and SLA
        priority = complaint.priority
        if priority:
            # ESCALATION: Critical priority
            if priority.priority_level == PriorityLevel.CRITICAL:
                guardrails_applied.append("critical_priority")
                risk_factors.append("Critical priority level")
            
            # ESCALATION: SLA breached + complaint
            if priority.sla_breached and priority.priority_level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]:
                guardrails_applied.append("sla_breach_high_priority")
                risk_factors.append("SLA breached with high priority")
                return SupervisorDecision(
                    decision=SupervisorDecisionEnum.HUMAN_APPROVAL,
                    reasoning="SLA breached - requires management attention",
                    confidence=0.85,
                    guardrails_applied=guardrails_applied,
                    risk_factors=risk_factors,
                )
        
        # Check if repeat complaint
        analysis = complaint.analysis
        if analysis and "repeat" in analysis.key_issues:
            guardrails_applied.append("repeat_complaint")
            risk_factors.append("Repeat complaint detected")
        
        # If no guardrails triggered, return None for LLM decision
        if not guardrails_applied:
            return None
        
        # Some guardrails applied but not escalation-level
        logger.info(f"Guardrails applied: {guardrails_applied}")
        return None

    async def _llm_decide(
        self,
        complaint: Complaint,
        db: Session,
    ) -> SupervisorDecision:
        """Use LLM to make routing decision."""
        
        prompt = self._build_prompt(complaint, db)
        
        response = await self.llm.generate_structured(
            prompt=prompt,
            schema=SupervisorDecision,
            temperature=0.5,  # Lower temperature for more consistent decisions
        )
        
        data = response.data
        decision = SupervisorDecision(**data)
        
        return decision

    def _build_prompt(self, complaint: Complaint, db: Session) -> str:
        """Build prompt for routing decision."""
        
        analysis = complaint.analysis
        priority = complaint.priority
        recommendation = db.query(ResolutionRecommendation).filter(
            ResolutionRecommendation.complaint_id == complaint.id
        ).first()
        
        recommendation_data = None
        if recommendation:
            recommendation_data = {
                "recommended_action": recommendation.recommended_action,
                "confidence": recommendation.confidence,
                "compensation": recommendation.compensation,
                "requires_human_review": recommendation.requires_human_review,
                "policy_evidence_available": bool(recommendation.policy_evidence),
                "policy_confidence": recommendation.policy_confidence,
            }
        
        return PromptTemplates.SUPERVISOR.decide_routing(
            complaint_text=complaint.raw_text,
            category=analysis.category if analysis else "unknown",
            sentiment=str(analysis.sentiment) if analysis else "unknown",
            recommendation=recommendation_data,
            policy_evidence_available=bool(recommendation_data and recommendation_data.get("policy_evidence_available")),
        )
