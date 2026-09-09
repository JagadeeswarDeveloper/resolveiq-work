"""Complaint service - business logic for complaints."""

from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
import json
import logging

from app.models import (
    Complaint, Customer, ComplaintAnalysis, ComplaintPriority, 
    ComplaintEvent, ARCStage, Channel, ComplaintStatus, Sentiment, 
    Severity, PriorityLevel, ResolutionRecommendation, SupervisorDecision
)
from app.schemas import ComplaintCreate
from app.agents.understanding_agent import UnderstandingAgent
from app.agents.resolution_agent import ResolutionAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.ai.llm import client as llm_client_module
from app.core.config import settings
from app.rag.service import ensure_demo_policies

logger = logging.getLogger(__name__)


class ComplaintService:
    """Service for complaint operations."""

    async def create_complaint(self, db: Session, complaint_data: ComplaintCreate):
        """Create a new complaint."""
        
        # Find or create customer
        customer = None
        if complaint_data.customer_id:
            customer = db.query(Customer).filter(Customer.id == complaint_data.customer_id).first()
        elif complaint_data.customer_email:
            customer = db.query(Customer).filter(Customer.email == complaint_data.customer_email).first()
            
        if not customer and complaint_data.customer_email:
            # Create new customer
            customer = Customer(
                name="Customer",
                email=complaint_data.customer_email,
                tier="standard",
                account_status="active",
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        elif not customer:
            raise ValueError("Customer not found and no email provided")
        
        # Create complaint
        complaint = Complaint(
            customer_id=customer.id,
            channel=complaint_data.channel,
            raw_text=complaint_data.raw_text,
            status=ComplaintStatus.RECEIVED,
            language=complaint_data.language,
        )
        
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        
        # Log first ARC event - CAPTURE
        arc_event = ComplaintEvent(
            complaint_id=complaint.id,
            arc_stage=ARCStage.CAPTURE,
            status="completed",
            timestamp=datetime.utcnow(),
        )
        db.add(arc_event)
        db.commit()
        
        return complaint

    async def run_demo_workflow(self, db: Session):
        """Run the demo with deterministic AI output regardless of live provider state."""
        previous_mode = settings.ai_mode
        previous_client = llm_client_module._llm_client
        settings.ai_mode = "demo"
        llm_client_module._llm_client = None
        try:
            await ensure_demo_policies(db)
            return await self._run_demo_workflow(db)
        finally:
            settings.ai_mode = previous_mode
            llm_client_module._llm_client = previous_client

    async def _run_demo_workflow(self, db: Session):
        """Run the deterministic demo through the persisted orchestration graph."""
        demo_email = "demo@resolveiq.local"
        demo_text = "I've already contacted support twice. My order was supposed to arrive five days ago and nobody is helping me."
        customer = db.query(Customer).filter(Customer.email == demo_email).first()
        if not customer:
            customer = Customer(name="ResolveIQ Demo Customer", email=demo_email, tier="gold", account_status="active")
            db.add(customer)
            db.commit()
            db.refresh(customer)

        complaint = db.query(Complaint).filter(
            Complaint.customer_id == customer.id,
            Complaint.raw_text == demo_text,
        ).first()
        if not complaint:
            complaint = await self.create_complaint(db, ComplaintCreate(
                customer_id=customer.id,
                channel=Channel.EMAIL.value,
                raw_text=demo_text,
            ))

        from app.workflows import ComplaintGraph
        await ComplaintGraph(self).run(db, complaint.id)

        db.refresh(complaint)
        return complaint

    async def list_complaints(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 50,
        status: str = None,
        customer_id: str = None,
    ):
        """List complaints with filtering."""
        query = db.query(Complaint)
        
        if status:
            query = query.filter(Complaint.status == status)
        
        if customer_id:
            query = query.filter(Complaint.customer_id == customer_id)
        
        complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
        return complaints

    async def get_complaint(self, db: Session, complaint_id: UUID):
        """Get complaint by ID."""
        return db.query(Complaint).filter(Complaint.id == complaint_id).first()

    async def analyze_complaint(self, db: Session, complaint_id: UUID):
        """Analyze complaint (extract entities, classify, sentiment)."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        try:
            # Use UnderstandingAgent for AI-powered analysis
            agent = UnderstandingAgent()
            analysis = await agent.analyze(db, complaint)
            
            # Update complaint status
            complaint.status = ComplaintStatus.CLASSIFIED
            
            # Add ARC event
            arc_event = ComplaintEvent(
                complaint_id=complaint.id,
                arc_stage=ARCStage.UNDERSTAND,
                status="completed",
                timestamp=datetime.utcnow(),
            )
            db.add(arc_event)
            db.commit()
            
            logger.info(f"Analyzed complaint {complaint_id} with category: {analysis.category}")
            
            return {
                "analysis_id": str(analysis.id),
                "category": analysis.category,
                "subcategory": analysis.subcategory,
                "sentiment": analysis.sentiment,
                "sentiment_score": analysis.sentiment_score,
                "severity": analysis.severity,
                "summary": analysis.summary,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing complaint {complaint_id}: {e}")
            # Fallback: create basic analysis
            analysis = ComplaintAnalysis(
                complaint_id=complaint.id,
                category="general",
                sentiment=Sentiment.NEUTRAL,
                sentiment_score=0.5,
                severity=Severity.MEDIUM,
                summary="Analysis failed - manual review needed",
                key_issues=["analysis_error"],
            )
            db.add(analysis)
            complaint.status = ComplaintStatus.CLASSIFIED
            
            arc_event = ComplaintEvent(
                complaint_id=complaint.id,
                arc_stage=ARCStage.UNDERSTAND,
                status="failed",
                timestamp=datetime.utcnow(),
            )
            db.add(arc_event)
            db.commit()
            
            return {
                "error": str(e),
                "analysis_id": str(analysis.id),
                "fallback": True,
            }

    async def prioritize_complaint(self, db: Session, complaint_id: UUID):
        """Calculate priority for complaint."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        # Get analysis for factors
        analysis = complaint.analysis
        if not analysis:
            return None
        
        # Calculate priority score (0-100)
        priority_score = 50
        reasons = []
        complaint_text = complaint.raw_text.lower()
        account_security_risk = any(term in complaint_text for term in (
            "unauthorized", "account takeover", "changed the email", "payment method",
            "don't recognize", "do not recognize", "can't log in", "cannot log in",
        )) or analysis.category == "account" and analysis.severity in [Severity.HIGH, Severity.CRITICAL]

        if account_security_risk:
            priority_score += 25
            reasons.append("Potential account takeover or unauthorized payment activity")
        
        # Sentiment factor
        if analysis.sentiment == Sentiment.HIGHLY_NEGATIVE:
            priority_score += 25
            reasons.append("Highly frustrated sentiment")
        elif analysis.sentiment == Sentiment.NEGATIVE:
            priority_score += 15
            reasons.append("Negative sentiment")
        
        # Severity factor
        if analysis.severity == Severity.CRITICAL:
            priority_score += 20
            reasons.append("Critical severity")
        elif analysis.severity == Severity.HIGH:
            priority_score += 10
            reasons.append("High severity")
        
        # Repeat complaint check
        prev_count = db.query(Complaint).filter(
            Complaint.customer_id == complaint.customer_id,
            Complaint.id != complaint.id,
        ).count()
        
        if prev_count > 0:
            priority_score += 10
            reasons.append(f"Repeat complaint (previous: {prev_count})")
        
        # Customer tier factor
        customer = complaint.customer
        if customer.tier == "platinum":
            priority_score += 15
            reasons.append("High-value customer")
        
        priority_level = PriorityLevel.LOW
        if account_security_risk:
            priority_level = PriorityLevel.CRITICAL
        elif priority_score >= 80:
            priority_level = PriorityLevel.CRITICAL
        elif priority_score >= 60:
            priority_level = PriorityLevel.HIGH
        elif priority_score >= 40:
            priority_level = PriorityLevel.MEDIUM
        
        priority = ComplaintPriority(
            complaint_id=complaint.id,
            priority_score=min(100, priority_score),
            priority_level=priority_level,
            severity_factor=0.3 if analysis.severity == Severity.HIGH else 0.1,
            sentiment_factor=0.3 if analysis.sentiment in [Sentiment.NEGATIVE, Sentiment.HIGHLY_NEGATIVE] else 0.1,
            customer_value_factor=0.3 if customer.tier == "platinum" else 0.1,
            repeat_complaint_factor=0.2 if prev_count > 0 else 0.0,
            reasons=reasons,
        )
        
        db.add(priority)
        complaint.status = ComplaintStatus.PRIORITIZED
        
        arc_event = ComplaintEvent(
            complaint_id=complaint.id,
            arc_stage=ARCStage.PRIORITIZE,
            status="completed",
            timestamp=datetime.utcnow(),
        )
        db.add(arc_event)
        db.commit()
        
        return {
            "priority_score": priority.priority_score,
            "priority_level": priority.priority_level,
            "reasons": reasons,
        }

    async def investigate_complaint(self, db: Session, complaint_id: UUID):
        """Investigate complaint (find related, duplicates, etc)."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        # Find related complaints (same customer, recent)
        related = db.query(Complaint).filter(
            Complaint.customer_id == complaint.customer_id,
            Complaint.id != complaint.id,
            Complaint.created_at >= (complaint.created_at - timedelta(days=30)),
        ).all()
        
        complaint.status = ComplaintStatus.INVESTIGATING

        from app.services.incident_detection_service import IncidentDetectionService
        detected_incidents = await IncidentDetectionService().detect(db)
        
        arc_event = ComplaintEvent(
            complaint_id=complaint.id,
            arc_stage=ARCStage.INVESTIGATE,
            status="completed",
            timestamp=datetime.utcnow(),
        )
        db.add(arc_event)
        db.commit()
        
        return {
            "related_complaints": len(related),
            "related_ids": [str(c.id) for c in related],
            "potential_incident": True if len(related) > 2 else False,
            "detected_incidents": [str(incident.id) for incident in detected_incidents if complaint in incident.complaints],
        }

    async def generate_resolution(self, db: Session, complaint_id: UUID):
        """Generate resolution recommendation."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        try:
            # Use ResolutionAgent for AI-powered recommendation
            agent = ResolutionAgent()
            recommendation = await agent.generate_recommendation(db, complaint)
            
            complaint.status = ComplaintStatus.RESOLUTION_PROPOSED
            
            arc_event = ComplaintEvent(
                complaint_id=complaint.id,
                arc_stage=ARCStage.REASON,
                status="completed",
                timestamp=datetime.utcnow(),
            )
            db.add(arc_event)
            db.commit()
            
            logger.info(f"Generated resolution for complaint {complaint_id}: {recommendation.recommended_action}")
            
            return {
                "recommendation_id": str(recommendation.id),
                "recommended_action": recommendation.recommended_action,
                "customer_response": recommendation.customer_response,
                "compensation": recommendation.compensation,
                "confidence": recommendation.confidence,
                "requires_human_review": recommendation.requires_human_review,
                "reasoning": recommendation.reasoning_summary,
            }
            
        except Exception as e:
            logger.error(f"Error generating resolution for {complaint_id}: {e}")
            # Fallback: suggest manual review
            return {
                "error": str(e),
                "fallback": True,
                "recommended_action": "Manual review required",
                "requires_human_review": True,
            }

    async def supervisor_route_complaint(self, db: Session, complaint_id: UUID):
        """Use supervisor to route complaint to appropriate action."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        try:
            # Use SupervisorAgent for routing decision
            agent = SupervisorAgent()
            decision = await agent.decide_routing(db, complaint)
            
            # Store decision
            supervisor_decision = SupervisorDecision(
                complaint_id=complaint.id,
                decision=decision.decision,
                reasoning=decision.reasoning,
                confidence=decision.confidence,
                guardrails_applied=decision.guardrails_applied,
                risk_factors=decision.risk_factors,
                escalation_reason=decision.escalation_reason,
            )
            db.add(supervisor_decision)
            
            # Update complaint status based on decision
            from app.ai.models import SupervisorDecisionEnum
            if decision.decision == SupervisorDecisionEnum.AUTO_RESOLVE:
                complaint.status = ComplaintStatus.RESOLVED
                complaint.resolved_at = datetime.utcnow()
            elif decision.decision == SupervisorDecisionEnum.HUMAN_APPROVAL:
                complaint.status = ComplaintStatus.PENDING_APPROVAL
            elif decision.decision == SupervisorDecisionEnum.ESCALATE:
                complaint.status = ComplaintStatus.ESCALATED
            
            # Add ARC event
            arc_event = ComplaintEvent(
                complaint_id=complaint.id,
                arc_stage=ARCStage.RESOLVE,
                status="completed",
                timestamp=datetime.utcnow(),
            )
            db.add(arc_event)
            db.commit()
            
            logger.info(f"Supervisor routed complaint {complaint_id} to {decision.decision}")
            
            return {
                "decision": decision.decision,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "guardrails": decision.guardrails_applied,
                "risk_factors": decision.risk_factors,
            }
            
        except Exception as e:
            logger.error(f"Error routing complaint {complaint_id}: {e}")
            # Default to human approval on error
            complaint.status = ComplaintStatus.PENDING_APPROVAL
            
            arc_event = ComplaintEvent(
                complaint_id=complaint.id,
                arc_stage=ARCStage.RESOLVE,
                status="failed",
                timestamp=datetime.utcnow(),
            )
            db.add(arc_event)
            db.commit()
            
            return {
                "error": str(e),
                "default_routing": "HUMAN_APPROVAL",
            }

    async def approve_complaint(self, db: Session, complaint_id: UUID):
        """Approve and resolve complaint."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        complaint.status = ComplaintStatus.RESOLVED
        complaint.resolved_at = datetime.utcnow()
        
        arc_event = ComplaintEvent(
            complaint_id=complaint.id,
            arc_stage=ARCStage.RESOLVE,
            status="completed",
            timestamp=datetime.utcnow(),
        )
        db.add(arc_event)
        db.commit()
        
        return {"status": "resolved", "resolved_at": complaint.resolved_at}

    async def escalate_complaint(self, db: Session, complaint_id: UUID):
        """Escalate complaint."""
        complaint = await self.get_complaint(db, complaint_id)
        if not complaint:
            return None
        
        complaint.status = ComplaintStatus.ESCALATED
        db.commit()
        
        return {"status": "escalated"}
