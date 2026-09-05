"""Incident service - business logic for incidents."""

from sqlalchemy.orm import Session
from uuid import UUID

from app.models import Incident, IncidentStatus, IncidentEvidence, ComplaintCluster
from app.services.incident_detection_service import IncidentDetectionService


class IncidentService:
    """Service for incident operations."""

    async def list_incidents(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 50,
        status: str = None,
    ):
        """List incidents."""
        query = db.query(Incident)
        
        if status:
            query = query.filter(Incident.status == status)
        
        incidents = query.order_by(Incident.detected_at.desc()).offset(skip).limit(limit).all()
        return incidents

    async def get_incident(self, db: Session, incident_id: UUID):
        """Get incident by ID."""
        return db.query(Incident).filter(Incident.id == incident_id).first()

    async def get_incident_complaints(self, db: Session, incident_id: UUID):
        """Get complaints linked to incident."""
        incident = await self.get_incident(db, incident_id)
        if not incident:
            return []
        
        return [
            {
                "id": str(c.id),
                "customer_id": str(c.customer_id),
                "channel": c.channel,
                "status": c.status,
                "created_at": c.created_at,
            }
            for c in incident.complaints
        ]

    async def detect(self, db: Session):
        return await IncidentDetectionService().detect(db)

    async def get_evidence(self, db: Session, incident_id: UUID):
        return db.query(IncidentEvidence).filter(
            IncidentEvidence.incident_id == incident_id
        ).order_by(IncidentEvidence.detection_timestamp.desc()).all()

    async def list_clusters(self, db: Session, skip: int = 0, limit: int = 50):
        return db.query(ComplaintCluster).order_by(
            ComplaintCluster.last_updated_at.desc()
        ).offset(skip).limit(limit).all()

    async def get_cluster(self, db: Session, cluster_id: UUID):
        return db.query(ComplaintCluster).filter(ComplaintCluster.id == cluster_id).first()
