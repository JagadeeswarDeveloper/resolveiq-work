"""Dashboard service - business logic for dashboard metrics."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models import Complaint, ComplaintStatus, ComplaintAnalysis, Incident, ComplaintPriority, SupervisorDecision


class DashboardService:
    """Service for dashboard operations."""

    async def get_summary(self, db: Session):
        """Get dashboard summary statistics."""
        total_complaints = db.query(Complaint).count()
        open_complaints = db.query(Complaint).filter(
            Complaint.status.in_([
                ComplaintStatus.RECEIVED,
                ComplaintStatus.NORMALIZED,
                ComplaintStatus.CLASSIFIED,
                ComplaintStatus.PRIORITIZED,
                ComplaintStatus.INVESTIGATING,
                ComplaintStatus.RESOLUTION_PROPOSED,
                ComplaintStatus.PENDING_APPROVAL,
            ])
        ).count()
        
        high_priority = db.query(ComplaintPriority).filter(ComplaintPriority.priority_score >= 60).count()
        
        resolved = db.query(Complaint).filter(
            Complaint.status == ComplaintStatus.RESOLVED,
            Complaint.resolved_at.isnot(None)
        ).all()
        
        avg_resolution_hours = 24.0  # Mock
        if resolved:
            total_hours = 0
            for r in resolved:
                if r.resolved_at:
                    duration = r.resolved_at - r.created_at
                    total_hours += duration.total_seconds() / 3600
            avg_resolution_hours = total_hours / len(resolved)
        
        sla_total = db.query(ComplaintPriority).count()
        sla_breaches = db.query(ComplaintPriority).filter(ComplaintPriority.sla_breached.is_(True)).count()
        decisions = db.query(SupervisorDecision).count()
        auto_resolved = db.query(SupervisorDecision).filter(SupervisorDecision.decision == "AUTO_RESOLVE").count()
        human_approval = db.query(SupervisorDecision).filter(SupervisorDecision.decision == "HUMAN_APPROVAL").count()
        active_incidents = db.query(Incident).filter(
            Incident.status.in_([
                "detected",
                "investigating",
                "confirmed",
            ])
        ).count()
        
        return {
            "total_complaints": total_complaints,
            "open_complaints": open_complaints,
            "high_priority_complaints": high_priority,
            "avg_resolution_time_hours": round(avg_resolution_hours, 1),
            "sla_breach_rate": round(sla_breaches / sla_total, 3) if sla_total else 0.0,
            "auto_resolution_rate": round(auto_resolved / decisions, 3) if decisions else 0.0,
            "human_approval_rate": round(human_approval / decisions, 3) if decisions else 0.0,
            "sla_breaches": sla_breaches,
            "active_incidents": active_incidents,
        }

    async def get_trends(self, db: Session, days: int = 7):
        """Get complaint volume trends."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            count = db.query(func.count(Complaint.id)).filter(
                func.date(Complaint.created_at) == date
            ).scalar() or 0
            trends.append({
                "date": date.isoformat(),
                "count": count,
            })
        
        return trends

    async def get_category_distribution(self, db: Session):
        """Get complaint distribution by category."""
        categories = db.query(
            ComplaintAnalysis.category,
            func.count(ComplaintAnalysis.id).label("count")
        ).group_by(ComplaintAnalysis.category).all()
        
        return [
            {"category": cat or "unclassified", "count": count}
            for cat, count in categories
        ]

    async def get_severity_distribution(self, db: Session):
        """Get complaint distribution by severity."""
        severities = db.query(
            ComplaintAnalysis.severity,
            func.count(ComplaintAnalysis.id).label("count")
        ).group_by(ComplaintAnalysis.severity).all()
        
        return [
            {"severity": sev or "unknown", "count": count}
            for sev, count in severities
        ]

    async def get_channel_distribution(self, db: Session):
        """Get complaint distribution by channel."""
        channels = db.query(
            Complaint.channel,
            func.count(Complaint.id).label("count")
        ).group_by(Complaint.channel).all()
        
        return [
            {"channel": channel, "count": count}
            for channel, count in channels
        ]
