"""Complaints API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models import Complaint, Customer
from app.schemas import ComplaintCreate, ComplaintResponse, ComplaintListItem, APIResponse
from app.services.complaint_service import ComplaintService

router = APIRouter()
complaint_service = ComplaintService()


@router.post("", response_model=ComplaintResponse)
async def create_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db),
):
    """Create a new complaint."""
    return await complaint_service.create_complaint(db, complaint)


@router.post("/demo", response_model=ComplaintResponse)
async def run_demo_complaint(db: Session = Depends(get_db)):
    """Create or reuse the stable demo complaint and run its workflow."""
    return await complaint_service.run_demo_workflow(db)


@router.get("", response_model=list[ComplaintListItem])
async def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None),
    customer_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """List complaints with pagination and filtering."""
    return await complaint_service.list_complaints(db, skip, limit, status, customer_id)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Get complaint by ID."""
    complaint = await complaint_service.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.post("/{complaint_id}/analyze", response_model=APIResponse)
async def analyze_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Analyze complaint (classify, extract entities, etc)."""
    result = await complaint_service.analyze_complaint(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Complaint analyzed", data=result)


@router.post("/{complaint_id}/prioritize", response_model=APIResponse)
async def prioritize_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Prioritize complaint."""
    result = await complaint_service.prioritize_complaint(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Complaint prioritized", data=result)


@router.post("/{complaint_id}/investigate", response_model=APIResponse)
async def investigate_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Investigate complaint (find related complaints, incidents, etc)."""
    result = await complaint_service.investigate_complaint(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Complaint investigated", data=result)


@router.post("/{complaint_id}/resolve", response_model=APIResponse)
async def resolve_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Generate resolution recommendation."""
    result = await complaint_service.generate_resolution(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Resolution generated", data=result)


@router.post("/{complaint_id}/route", response_model=APIResponse)
async def route_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Use supervisor agent to route complaint (decision: auto-resolve, approval, escalate)."""
    result = await complaint_service.supervisor_route_complaint(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Complaint routed", data=result)


@router.post("/{complaint_id}/approve", response_model=APIResponse)
async def approve_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Approve and resolve complaint."""
    result = await complaint_service.approve_complaint(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Complaint approved and resolved", data=result)


@router.post("/{complaint_id}/escalate", response_model=APIResponse)
async def escalate_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
):
    """Escalate complaint."""
    result = await complaint_service.escalate_complaint(db, complaint_id)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return APIResponse(success=True, message="Complaint escalated", data=result)
