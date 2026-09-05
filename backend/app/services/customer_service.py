"""Customer service - business logic for customers."""

from sqlalchemy.orm import Session
from uuid import UUID

from app.models import Customer, Complaint, Order
from app.schemas import CustomerCreate, CustomerResponse


class CustomerService:
    """Service for customer operations."""

    async def create_customer(self, db: Session, customer_data: CustomerCreate):
        """Create a new customer."""
        # Check if customer with email already exists
        existing = db.query(Customer).filter(Customer.email == customer_data.email).first()
        if existing:
            return existing
        
        customer = Customer(
            external_id=customer_data.external_id,
            name=customer_data.name,
            email=customer_data.email,
            phone=customer_data.phone,
            tier=customer_data.tier,
            account_status=customer_data.account_status,
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    async def list_customers(self, db: Session, skip: int = 0, limit: int = 50):
        """List customers."""
        return db.query(Customer).offset(skip).limit(limit).all()

    async def get_customer(self, db: Session, customer_id: UUID):
        """Get customer by ID."""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    async def get_customer_by_email(self, db: Session, email: str):
        """Get customer by email."""
        return db.query(Customer).filter(Customer.email == email).first()

    async def get_customer_complaints(self, db: Session, customer_id: UUID):
        """Get customer's complaints."""
        complaints = db.query(Complaint).filter(Complaint.customer_id == customer_id).all()
        return [
            {
                "id": str(c.id),
                "channel": c.channel,
                "status": c.status,
                "created_at": c.created_at,
                "raw_text": c.raw_text[:100],
            }
            for c in complaints
        ]

    async def get_customer_orders(self, db: Session, customer_id: UUID):
        """Get customer's orders."""
        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        return [
            {
                "id": str(o.id),
                "product": o.product,
                "status": o.status,
                "amount": o.amount,
                "order_date": o.order_date,
                "expected_delivery": o.expected_delivery_date,
            }
            for o in orders
        ]
