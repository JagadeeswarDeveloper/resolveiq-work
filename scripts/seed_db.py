"""Seed database with demo data."""

import os
import sys
from datetime import datetime, timedelta
import random
import uuid
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.models import (
    Customer, Order, Complaint, ComplaintAnalysis, ComplaintPriority,
    ComplaintEvent, ARCStage, Channel, ComplaintStatus, Sentiment, Severity,
    PriorityLevel, Incident, KnowledgeDocument, KnowledgeChunk
)
from app.rag.ingestion import ingest_document
from app.services.incident_detection_service import IncidentDetectionService


def seed_database():
    """Seed the database with demo data."""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Complaint).delete()
        db.query(Order).delete()
        db.query(Customer).delete()
        db.query(Incident).delete()
        db.query(KnowledgeDocument).delete()
        db.commit()
        
        print("✓ Cleared existing data")
        
        # Create customers
        customers = []
        customer_data = [
            ("john.doe@example.com", "John Doe", "platinum", 5000.00),
            ("jane.smith@example.com", "Jane Smith", "gold", 2000.00),
            ("bob.johnson@example.com", "Bob Johnson", "standard", 500.00),
            ("alice.williams@example.com", "Alice Williams", "gold", 3000.00),
            ("charlie.brown@example.com", "Charlie Brown", "standard", 300.00),
            ("diana.princess@example.com", "Diana Princess", "platinum", 7500.00),
            ("evan.rocks@example.com", "Evan Rocks", "standard", 150.00),
            ("fiona.apple@example.com", "Fiona Apple", "gold", 2500.00),
            ("george.wilson@example.com", "George Wilson", "standard", 400.00),
            ("hannah.montana@example.com", "Hannah Montana", "platinum", 6000.00),
        ]
        
        for email, name, tier, lifetime_value in customer_data:
            customer = Customer(
                external_id=f"CUST-{uuid.uuid4().hex[:8].upper()}",
                name=name,
                email=email,
                phone=f"+1 555-{random.randint(1000, 9999)}",
                tier=tier,
                account_status="active",
                lifetime_value=lifetime_value,
                complaints_count=0,
            )
            db.add(customer)
            customers.append(customer)
        
        db.commit()
        print(f"✓ Created {len(customers)} customers")
        
        # Create orders
        orders = []
        products = [
            ("Laptop Pro", "electronics", 1299.99),
            ("USB-C Cable", "accessories", 19.99),
            ("Wireless Mouse", "accessories", 49.99),
            ("Monitor 4K", "electronics", 599.99),
            ("Keyboard RGB", "accessories", 129.99),
            ("Webcam HD", "electronics", 89.99),
            ("Desk Lamp", "furniture", 39.99),
            ("Desk Chair", "furniture", 299.99),
            ("Phone Stand", "accessories", 14.99),
            ("USB Hub", "accessories", 29.99),
        ]
        
        for customer in customers * 6:  # Multiple orders per customer
            product, category, price = random.choice(products)
            order_date = datetime.utcnow() - timedelta(days=random.randint(1, 60))
            expected_delivery = order_date + timedelta(days=random.randint(3, 14))
            
            # Some delivered, some in transit
            status = random.choice(["delivered", "shipped", "pending", "cancelled"])
            if status == "delivered":
                actual_delivery = expected_delivery + timedelta(days=random.randint(0, 5))
            else:
                actual_delivery = None
            
            order = Order(
                external_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                customer_id=customer.id,
                product=product,
                product_category=category,
                order_date=order_date,
                expected_delivery_date=expected_delivery,
                actual_delivery_date=actual_delivery,
                amount=price,
                status=status,
                shipping_address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Pine'])} St",
            )
            db.add(order)
            orders.append(order)
        
        db.commit()
        print(f"✓ Created {len(orders)} orders")
        
        # Create complaints - various types
        complaint_templates = [
            ("Email", "I ordered a laptop 2 weeks ago and it still hasn't arrived. I've called support twice and no one is helping me. Very disappointed."),
            ("Ticket", "The USB-C cable I received is broken. It doesn't charge my phone properly."),
            ("Web Form", "Charged twice for my order. Please refund immediately."),
            ("Chat", "The monitor won't power on. Defective product."),
            ("Email", "Been waiting 20 days for a desk chair. The website said 5-7 days delivery."),
            ("Phone", "Your customer service is terrible. Put me on hold for 45 minutes."),
            ("Social Media", "Worst experience ever! Defective keyboard, no response from support."),
            ("Email", "The package arrived damaged. Product is unusable."),
            ("Ticket", "Wrong items shipped. Ordered a mouse, got a cable instead."),
            ("Web Form", "Warranty claim denied without proper explanation."),
            ("Ticket", "Delivery address was incorrect and no one called to confirm."),
            ("Email", "This is my third complaint about this product. Still no resolution."),
            ("Chat", "Please cancel my order but website won't let me."),
            ("Email", "Product quality is terrible. Much worse than advertised."),
            ("Ticket", "Shipping cost was not displayed until checkout."),
        ]
        
        complaints = []
        now = datetime.utcnow()

        # Ground-truth cohort for the incident intelligence demo.
        for i in range(18):
            customer = customers[i % len(customers)]
            complaint = Complaint(
                external_id=f"CMP-{uuid.uuid4().hex[:8].upper()}",
                customer_id=customer.id,
                channel=Channel.EMAIL,
                raw_text=f"My delivery from the Chennai fulfilment warehouse is five days late. Shipment {i} has not moved.",
                status=ComplaintStatus.CLASSIFIED,
                language="en",
                created_at=now - timedelta(hours=i),
            )
            db.add(complaint)
            complaints.append(complaint)
        
        for i in range(82):
            customer = random.choice(customers)
            channel, text = random.choice(complaint_templates)
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
            
            channel_value = channel.lower().replace(" ", "_")
            complaint = Complaint(
                external_id=f"CMP-{uuid.uuid4().hex[:8].upper()}",
                customer_id=customer.id,
                channel=Channel(channel_value),
                raw_text=text,
                status=random.choice([
                    ComplaintStatus.RECEIVED,
                    ComplaintStatus.CLASSIFIED,
                    ComplaintStatus.PRIORITIZED,
                    ComplaintStatus.INVESTIGATING,
                    ComplaintStatus.RESOLVED,
                ]),
                language="en",
                created_at=created_at,
            )
            db.add(complaint)
            complaints.append(complaint)
        
        db.commit()
        print(f"✓ Created {len(complaints)} complaints")
        
        # Add analysis to complaints
        for index, complaint in enumerate(complaints):
            sentiment_scores = [Sentiment.NEGATIVE, Sentiment.HIGHLY_NEGATIVE, Sentiment.NEUTRAL]
            sentiment = random.choice(sentiment_scores + [Sentiment.NEGATIVE] * 7)  # Bias towards negative
            severity = random.choice([Severity.MEDIUM, Severity.HIGH, Severity.LOW, Severity.CRITICAL])
            
            is_logistics_cohort = index < 18
            analysis = ComplaintAnalysis(
                complaint_id=complaint.id,
                category="delivery" if is_logistics_cohort else random.choice(["delivery", "product_quality", "billing", "customer_service", "technical", "refund"]),
                subcategory=random.choice(["late", "damaged", "wrong_item", "defective", "overcharge"]),
                sentiment=sentiment,
                sentiment_score=0.2 if sentiment == Sentiment.NEGATIVE else 0.1 if sentiment == Sentiment.HIGHLY_NEGATIVE else 0.6,
                severity=severity,
                entities={"order_id": str(uuid.uuid4()), "product": "Laptop Pro", "region": "Chennai", "warehouse": "Chennai fulfilment warehouse"} if is_logistics_cohort else {"order_id": str(uuid.uuid4()), "product": "electronic device"},
                summary=complaint.raw_text[:100],
                key_issues=["delivery_delay", "poor_quality"] if severity == Severity.HIGH else ["minor_issue"],
            )
            db.add(analysis)
            
            # Add priority
            priority_score = random.randint(20, 95)
            priority_level = PriorityLevel.CRITICAL if priority_score > 75 else PriorityLevel.HIGH if priority_score > 50 else PriorityLevel.MEDIUM
            
            priority = ComplaintPriority(
                complaint_id=complaint.id,
                priority_score=priority_score,
                priority_level=priority_level,
                severity_factor=0.3 if severity == Severity.HIGH else 0.1,
                sentiment_factor=0.3 if sentiment in [Sentiment.NEGATIVE, Sentiment.HIGHLY_NEGATIVE] else 0.1,
                reasons=["High priority complaint"],
                sla_breached=priority_score > 70,
            )
            db.add(priority)
            
            # Add ARC events
            for stage in [ARCStage.CAPTURE, ARCStage.UNIFY]:
                arc_event = ComplaintEvent(
                    complaint_id=complaint.id,
                    arc_stage=stage,
                    status="completed",
                    timestamp=complaint.created_at + timedelta(minutes=random.randint(1, 30)),
                )
                db.add(arc_event)
        
        db.commit()
        print("✓ Added analysis and priority to complaints")
        
        detected_incidents = asyncio.run(IncidentDetectionService().detect(db))
        print(f"✓ Detected {len(detected_incidents)} potential incident(s)")
        
        # Create knowledge documents
        policies = [
            (
                "Refund Policy",
                "30-day money-back guarantee",
                "refund_policy",
                "policy",
                "billing",
                "Items can be returned within 30 days for a full refund. Items must be in original condition.",
            ),
            (
                "Delivery SLA",
                "Delivery time guarantee",
                "delivery_sla",
                "slo",
                "delivery",
                "Standard delivery: 5-7 business days. Express delivery: 2-3 business days. If not delivered by promised date, customer receives $20 credit.",
            ),
            (
                "Compensation Policy",
                "Compensation for service failures",
                "compensation_policy",
                "policy",
                "customer_service",
                "Late delivery: Up to $50 credit. Damaged product: Full refund + $25 credit. Wrong item: Full refund + $15 credit + free shipping on replacement.",
            ),
            (
                "Escalation Procedure",
                "When and how to escalate complaints",
                "escalation_procedure",
                "sop",
                "customer_service",
                "Escalate if: Customer is Platinum tier, compensation exceeds $100, legal/safety concerns, regulatory issues.",
            ),
            (
                "Product FAQ",
                "Common product questions",
                "product_faq",
                "faq",
                "technical",
                "See product manual for detailed specifications. Common issues: Reset device, check drivers, verify connection.",
            ),
        ]
        
        for title, desc, doc_id, doc_type, category, content in policies:
            doc = KnowledgeDocument(
                title=title,
                description=desc,
                content=content,
                document_type=doc_type,
                category=category,
                version=1,
                is_active=True,
            )
            db.add(doc)
            db.flush()
            
            # Add chunks
            chunks = content.split(". ")
            for idx, chunk_text in enumerate(chunks):
                chunk = KnowledgeChunk(
                    document=doc,
                    chunk_index=idx,
                    content=chunk_text,
                    chunk_metadata={"section": title, "index": idx},
                )
                db.add(chunk)
        
        db.commit()
        for document in db.query(KnowledgeDocument).all():
            asyncio.run(ingest_document(db, document))
        print("✓ Created knowledge documents")
        
        print("\n✅ Demo data seeded successfully!")
        print(f"   Customers: {len(customers)}")
        print(f"   Orders: {len(orders)}")
        print(f"   Complaints: {len(complaints)}")
        print(f"   Incidents: 1")
        print(f"   Knowledge Documents: {len(policies)}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
