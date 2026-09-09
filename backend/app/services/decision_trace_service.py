from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Complaint


class DecisionTraceService:
    """Persist explainable decision steps for complaints."""

    def record_event(self, db: Session, complaint_id: str, step: str, source: str, result: str, confidence: float = 0.0) -> dict[str, Any]:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise ValueError("Complaint not found")
        trace = list(getattr(complaint, "decision_trace", []) or [])
        event = {
            "step": step,
            "source": source,
            "result": result,
            "confidence": float(confidence),
            "timestamp": datetime.utcnow().isoformat(),
        }
        trace.append(event)
        complaint.decision_trace = trace
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return type("DecisionTraceEntry", (), event)()

    def get_trace(self, db: Session, complaint_id: str) -> list[dict[str, Any]]:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return []
        return list(getattr(complaint, "decision_trace", []) or [])
