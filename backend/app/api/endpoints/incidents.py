"""Incidents API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas import IncidentResponse, IncidentEvidenceResponse, ComplaintClusterResponse, APIResponse
from app.services.incident_service import IncidentService

router = APIRouter()
cluster_router = APIRouter()
incident_service = IncidentService()


@router.post("/detect", response_model=list[IncidentResponse])
async def detect_incidents(db: Session = Depends(get_db)):
    """Detect or refresh potential incidents from recent complaints."""
    return await incident_service.detect(db)


@cluster_router.get("", response_model=list[ComplaintClusterResponse])
async def list_clusters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return await incident_service.list_clusters(db, skip, limit)


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """List incidents."""
    return await incident_service.list_incidents(db, skip, limit, status)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    """Get incident by ID."""
    incident = await incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/complaints")
async def get_incident_complaints(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    """Get complaints linked to incident."""
    complaints = await incident_service.get_incident_complaints(db, incident_id)
    return APIResponse(success=True, message="Complaints retrieved", data={"complaints": complaints})


@router.get("/{incident_id}/evidence", response_model=list[IncidentEvidenceResponse])
async def get_incident_evidence(incident_id: UUID, db: Session = Depends(get_db)):
    return await incident_service.get_evidence(db, incident_id)


@router.post("/{incident_id}/refresh", response_model=list[IncidentResponse])
async def refresh_incident(incident_id: UUID, db: Session = Depends(get_db)):
    incident = await incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incidents = await incident_service.detect(db)
    return [item for item in incidents if item.id == incident_id]


@cluster_router.get("/{cluster_id}", response_model=ComplaintClusterResponse)
async def get_cluster(cluster_id: UUID, db: Session = Depends(get_db)):
    cluster = await incident_service.get_cluster(db, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster
