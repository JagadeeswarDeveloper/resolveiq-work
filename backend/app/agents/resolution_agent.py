"""Resolution Agent - generates resolution recommendations."""

import logging
import time
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.models import (
    Complaint, Customer, ComplaintAnalysis, ComplaintPriority,
    ResolutionRecommendation, AgentExecution, ARCStage
)
from app.ai.llm.client import get_llm_client
from app.ai.models import ResolutionRecommendation as ResolutionRecommendationModel
from app.ai.prompts import PromptTemplates
from app.rag.service import retrieve_policy_evidence
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResolutionAgent:
    """AI agent for generating resolution recommendations."""

    def __init__(self):
        self.llm = get_llm_client()
        self.agent_name = "ResolutionAgent"

    async def generate_recommendation(
        self,
        db: Session,
        complaint: Complaint,
    ) -> ResolutionRecommendation:
        """Generate resolution recommendation."""
        
        execution_start = time.time()
        execution = AgentExecution(
            complaint_id=complaint.id,
            agent_name=self.agent_name,
            arc_stage=ARCStage.REASON,
            status="in_progress",
            started_at=datetime.utcnow(),
            is_demo_mode=self.llm.is_demo_mode(),
        )
        
        try:
            # Gather context
            customer = complaint.customer
            analysis = complaint.analysis
            priority = complaint.priority
            query = f"{complaint.raw_text} {analysis.category if analysis else ''}"
            policy_evidence = await retrieve_policy_evidence(db, query)
            execution.input_summary = {
                "query": query,
                "retrieved_document_ids": [item["document_id"] for item in policy_evidence],
                "retrieved_chunk_ids": [item["chunk_id"] for item in policy_evidence],
                "scores": [item["score"] for item in policy_evidence],
                "embedding_provider": settings.embedding_provider,
                "embedding_model": settings.embedding_model,
            }
            evidence_text = "\n".join(
                f"- {item['document']} ({item['metadata'].get('section', 'section')}): {item['content']} [score={item['score']}]"
                for item in policy_evidence
                if item["score"] > 0
            ) or "No policy evidence was retrieved."
            
            # Build prompt with all context
            prompt = self._build_prompt(complaint, customer, analysis, priority, evidence_text)
            
            logger.info(f"Resolution Agent generating recommendation for {complaint.id}")
            response = await self.llm.generate_structured(
                prompt=prompt,
                schema=ResolutionRecommendationModel,
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Validate response
            data = response.data
            data["policy_evidence"] = data.get("policy_evidence") or []
            data["policy_sources"] = data.get("policy_sources") or []
            rec_model = ResolutionRecommendationModel(**data)
            if not policy_evidence:
                rec_model.policy_evidence = []
                rec_model.policy_sources = []
                rec_model.policy_confidence = 0.0
                rec_model.requires_human_review = True

            account_security_risk = any(term in complaint.raw_text.lower() for term in (
                "account takeover", "unauthorized", "changed the email", "email address",
                "unrecognized payment", "payment method", "can't log in", "cannot log in",
                "do not recognize", "don't recognize",
            ))
            if account_security_risk:
                rec_model.requires_human_review = True
                rec_model.compensation = None
                if not any(term in rec_model.recommended_action.lower() for term in ("security", "verify", "account", "lock", "restrict")):
                    rec_model.recommended_action = "Escalate to a human security reviewer, restrict suspicious account activity, verify identity through a trusted channel, and investigate the unauthorized changes."
                rec_model.internal_actions = list(dict.fromkeys([
                    *rec_model.internal_actions,
                    "Restrict suspicious account activity",
                    "Verify identity through a trusted channel",
                    "Review login, email, and payment-method changes",
                    "Escalate to a human security reviewer",
                ]))
            
            # Keep one current recommendation per complaint so repeated runs
            # cannot leave stale recommendations for the detail view to read.
            recommendation = db.query(ResolutionRecommendation).filter(
                ResolutionRecommendation.complaint_id == complaint.id
            ).first()
            if not recommendation:
                recommendation = ResolutionRecommendation(complaint_id=complaint.id)
            recommendation.recommended_action = rec_model.recommended_action
            recommendation.customer_response = rec_model.customer_response
            recommendation.internal_actions = rec_model.internal_actions or []
            recommendation.compensation = rec_model.compensation.model_dump() if rec_model.compensation else None
            recommendation.reasoning_summary = rec_model.reasoning_summary
            recommendation.confidence = rec_model.confidence
            recommendation.requires_human_review = rec_model.requires_human_review
            recommendation.policy_sources = rec_model.policy_sources or [item["document"] for item in policy_evidence]
            recommendation.policy_evidence = policy_evidence
            recommendation.policy_confidence = rec_model.policy_confidence if policy_evidence else 0.0
            
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            
            # Record successful execution
            latency_ms = int((time.time() - execution_start) * 1000)
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = latency_ms
            execution.model_used = response.model
            execution.tokens_used = response.tokens_used
            execution.output_summary = {
                "action": recommendation.recommended_action,
                "confidence": recommendation.confidence,
                "requires_review": recommendation.requires_human_review,
                "policy_evidence_count": len(policy_evidence),
                "policy_sources": recommendation.policy_sources,
            }
            
            logger.info(f"Resolution Agent completed in {latency_ms}ms")
            
        except Exception as e:
            logger.error(f"Resolution Agent error: {e}")
            latency_ms = int((time.time() - execution_start) * 1000)
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = latency_ms
            execution.error_message = str(e)
            raise
        
        finally:
            db.add(execution)
            db.commit()
        
        return recommendation

    def _build_prompt(
        self,
        complaint: Complaint,
        customer: Customer,
        analysis: Optional[ComplaintAnalysis],
        priority: Optional[ComplaintPriority],
        policy_evidence: str = "No policy evidence was retrieved.",
    ) -> str:
        """Build prompt for resolution generation."""
        return PromptTemplates.RESOLUTION.generate_resolution(
            complaint_text=complaint.raw_text,
            category=analysis.category if analysis else "unknown",
            sentiment=str(analysis.sentiment) if analysis else "unknown",
            customer_tier=customer.tier,
            lifetime_value=customer.lifetime_value,
            previous_complaints=customer.complaints_count,
            policy_evidence=policy_evidence,
        )
