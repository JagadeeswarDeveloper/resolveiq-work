from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import Complaint, ResolutionRecommendation


class CriticAgent:
    """Bounded critic that validates proposed resolutions before supervisor routing."""

    def evaluate(self, db: Session, complaint_id: str) -> dict[str, Any]:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise ValueError("Complaint not found")

        recommendation = db.query(ResolutionRecommendation).filter(ResolutionRecommendation.complaint_id == complaint.id).first()
        policy_pass = recommendation is not None and bool(recommendation.policy_evidence)
        evidence_pass = complaint.analysis is not None and bool(complaint.analysis.summary)
        customer_pass = complaint.customer is not None and complaint.customer.name
        action_valid = recommendation is not None and bool(recommendation.recommended_action)
        hallucination = "LOW"
        if not policy_pass or not evidence_pass:
            hallucination = "HIGH"
        elif not action_valid:
            hallucination = "MEDIUM"

        result = {
            "policy_compliance": "PASS" if policy_pass else "FAIL",
            "evidence_support": "PASS" if evidence_pass else "FAIL",
            "customer_context": "PASS" if customer_pass else "FAIL",
            "action_validity": "PASS" if action_valid else "FAIL",
            "hallucination_risk": hallucination,
            "overall_recommendation": "PASS" if all([
                policy_pass,
                evidence_pass,
                customer_pass,
                action_valid,
            ]) else "REVISE",
            "review_required": hallucination in {"MEDIUM", "HIGH"},
        }
        return result
