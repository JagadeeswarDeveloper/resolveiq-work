from datetime import datetime, timedelta
import uuid
import asyncio

from app.models import (
    Customer, Complaint, ComplaintAnalysis, Channel, ComplaintCluster,
    Incident, Severity, Sentiment,
)
from app.services.incident_detection_service import IncidentDetectionService
from app.core.database import SessionLocal
from app.core.database import Base, engine


def test_detection_clusters_contextual_complaints_and_is_idempotent():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        customers = [Customer(name=f"Customer {i}", email=f"incident-{i}-{uuid.uuid4()}@example.com") for i in range(3)]
        db.add_all(customers)
        db.flush()
        for index, customer in enumerate(customers):
            complaint = Complaint(customer_id=customer.id, channel=Channel.EMAIL, raw_text=f"Delivery from Chennai warehouse is five days late {index}", created_at=datetime.utcnow() - timedelta(hours=index))
            db.add(complaint)
            db.flush()
            db.add(ComplaintAnalysis(complaint_id=complaint.id, category="delivery", severity=Severity.HIGH, sentiment=Sentiment.NEGATIVE, entities={"region": "Chennai", "product": "Laptop Pro"}))
        unrelated_customer = Customer(name="Billing Customer", email=f"billing-{uuid.uuid4()}@example.com")
        db.add(unrelated_customer)
        db.flush()
        unrelated = Complaint(customer_id=unrelated_customer.id, channel=Channel.EMAIL, raw_text="Billing charge is incorrect", created_at=datetime.utcnow())
        db.add(unrelated)
        db.flush()
        db.add(ComplaintAnalysis(complaint_id=unrelated.id, category="billing", entities={"region": "Chennai"}))
        db.commit()

        service = IncidentDetectionService()
        first = asyncio.run(service.detect(db))
        second = asyncio.run(service.detect(db))

        assert len(first) == 1
        assert first[0].status.value == "detected"
        assert first[0].complaint_count == 3
        assert len(second) == 1
        assert db.query(Incident).count() == 1
        assert db.query(ComplaintCluster).count() == 1
    finally:
        db.rollback()
        db.close()
