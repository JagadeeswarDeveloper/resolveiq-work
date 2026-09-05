"""Customers API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas import CustomerResponse, CustomerCreate, APIResponse
from app.services.customer_service import CustomerService

router = APIRouter()
customer_service = CustomerService()


@router.post("", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    """Create a new customer."""
    return await customer_service.create_customer(db, customer)


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List customers."""
    return await customer_service.list_customers(db, skip, limit)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    """Get customer by ID."""
    customer = await customer_service.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/complaints")
async def get_customer_complaints(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    """Get customer's complaints."""
    complaints = await customer_service.get_customer_complaints(db, customer_id)
    return APIResponse(success=True, message="Complaints retrieved", data={"complaints": complaints})


@router.get("/{customer_id}/orders")
async def get_customer_orders(
    customer_id: UUID,
    db: Session = Depends(get_db),
):
    """Get customer's orders."""
    orders = await customer_service.get_customer_orders(db, customer_id)
    return APIResponse(success=True, message="Orders retrieved", data={"orders": orders})
