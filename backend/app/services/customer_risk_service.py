from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.models import Complaint, ComplaintAnalysis, Customer, Order


class CustomerRiskService:
    """Deterministic customer risk scoring based on explainable evidence."""

    def score_customer(self, db: Session, customer_id: str) -> dict[str, Any]:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"risk_level": "LOW", "score": 0, "reasons": [], "customer_id": customer_id}

        complaints = db.query(Complaint).filter(Complaint.customer_id == customer.id).all()
        orders = db.query(Order).filter(Order.customer_id == customer.id).all()
        open_complaints = [item for item in complaints if item.status.value not in {"resolved", "closed"}]
        recent_negative = 0
        reasons = []
        score = 0

        if len(complaints) >= 2:
            score += 20
            reasons.append("Multiple complaints")
        if len(open_complaints) >= 1:
            score += 15
            reasons.append("Open complaint(s)")
        if len(orders) >= 3:
            score += 5
        for complaint in complaints:
            analysis = complaint.analysis
            if analysis and analysis.sentiment and analysis.sentiment.value in {"negative", "highly_negative"}:
                recent_negative += 1
            if complaint.priority and complaint.priority.priority_score and complaint.priority.priority_score >= 75:
                score += 10
                reasons.append("High-priority complaint")
            if complaint.priority and complaint.priority.sla_breached:
                score += 15
                reasons.append("SLA breach")

        if recent_negative >= 2:
            score += 15
            reasons.append("Repeated negative sentiment")
        if len(complaints) >= 4 or len(open_complaints) >= 2:
            score += 15
            reasons.append("Escalating service pattern")

        if score >= 65:
            risk_level = "HIGH"
        elif score >= 35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "customer_id": str(customer.id),
            "risk_level": risk_level,
            "score": min(score, 100),
            "reasons": reasons,
            "customer_tier": customer.tier,
            "open_complaints": len(open_complaints),
            "repeat_complaint_count": len(complaints) - 1,
            "order_count": len(orders),
            "details": {
                "complaint_count": len(complaints),
                "recent_negative_sentiment_count": recent_negative,
            },
        }
