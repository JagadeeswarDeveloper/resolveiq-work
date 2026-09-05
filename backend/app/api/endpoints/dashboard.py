"""Dashboard API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas import DashboardSummary, ComplaintTrendData, CategoryDistribution
from app.services.dashboard_service import DashboardService

router = APIRouter()
dashboard_service = DashboardService()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary statistics."""
    return await dashboard_service.get_summary(db)


@router.get("/trends", response_model=list[ComplaintTrendData])
async def get_complaint_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Get complaint volume trends."""
    return await dashboard_service.get_trends(db, days)


@router.get("/categories", response_model=list[CategoryDistribution])
async def get_category_distribution(
    db: Session = Depends(get_db),
):
    """Get complaint distribution by category."""
    return await dashboard_service.get_category_distribution(db)


@router.get("/severity-distribution")
async def get_severity_distribution(db: Session = Depends(get_db)):
    """Get complaint distribution by severity."""
    return await dashboard_service.get_severity_distribution(db)


@router.get("/channel-distribution")
async def get_channel_distribution(db: Session = Depends(get_db)):
    """Get complaint distribution by channel."""
    return await dashboard_service.get_channel_distribution(db)
