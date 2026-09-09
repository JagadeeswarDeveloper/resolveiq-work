import uuid
from datetime import datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.models import (
    Channel,
    Complaint,
    ComplaintAnalysis,
    ComplaintPriority,
    Customer,
    Incident,
    KnowledgeDocument,
    Order,
    ResolutionRecommendation,
    Severity,
    Sentiment,
)
from app.services.customer_risk_service import CustomerRiskService
from app.services.decision_trace_service import DecisionTraceService
from app.services.knowledge_graph_service import KnowledgeGraphService


def setup_test_data(db):
    customer = Customer(
        external_id=f"CUST-{uuid.uuid4().hex[:8]}",
        name="Test Customer",
        email=f"graph-risk-{uuid.uuid4().hex[:8]}@example.com",
        tier="gold",
        account_status="active",
    )
    db.add(customer)
    db.flush()

    order = Order(
        external_id=f"ORD-{uuid.uuid4().hex[:8]}",
        customer_id=customer.id,
        product="Laptop Pro 14",
        product_category="electronics",
        order_date=datetime.utcnow() - timedelta(days=15),
        amount=1499.0,
        status="shipped",
        shipping_address="Chennai, India",
    )
    db.add(order)
    db.flush()

    complaint = Complaint(
        external_id=f"CMP-{uuid.uuid4().hex[:8]}",
        customer_id=customer.id,
        channel=Channel.EMAIL,
        raw_text="My order from Chennai is late and I have raised this twice.",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(complaint)
    db.flush()

    db.add(ComplaintAnalysis(
        complaint_id=complaint.id,
        category="delivery",
        subcategory="late delivery",
        sentiment=Sentiment.NEGATIVE,
        sentiment_score=0.8,
        severity=Severity.HIGH,
        entities={"region": "Chennai", "product": "Laptop Pro 14", "order_id": str(order.id)},
        summary="Late delivery complaint",
    ))
    db.add(ComplaintPriority(
        complaint_id=complaint.id,
        priority_score=82,
        priority_level="high",
        sla_breached=True,
        reasons=["repeat complaint", "late delivery"],
    ))
    db.add(ResolutionRecommendation(
        complaint_id=complaint.id,
        recommended_action="Offer tracking update and service credit",
        reasoning_summary="Delay requires proactive update and possible service credit.",
        confidence=0.88,
        requires_human_review=False,
        policy_sources=["delivery policy"],
        policy_evidence=[{"document": "Delivery policy", "content": "Late delivery requires proactive customer update.", "score": 0.91}],
    ))

    incident = Incident(
        external_id=f"INC-{uuid.uuid4().hex[:8]}",
        title="Chennai fulfillment delay",
        description="Delay cluster",
        affected_regions=["Chennai"],
        affected_products=["Laptop Pro 14"],
        complaint_count=3,
        confidence=0.83,
        suspected_root_cause="carrier backlogs",
        potential_root_cause="carrier handoff backlog",
        evidence_summary="Likely regional shipping delay",
    )
    db.add(incident)
    db.flush()
    complaint.incidents.append(incident)

    policy = KnowledgeDocument(
        title="Delivery Recovery Policy",
        content="Late delivery requires tracking update and service credit when SLA is missed.",
        document_type="policy",
        category="delivery",
        source="demo",
    )
    db.add(policy)
    db.flush()
    return customer, complaint


def test_knowledge_graph_builds_entity_neighborhood():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        customer, complaint = setup_test_data(db)
        graph = KnowledgeGraphService().build_graph(db, center_type="customer", center_id=str(customer.id))
        assert graph["nodes"]
        assert any(node["type"] == "customer" and node["id"] == str(customer.id) for node in graph["nodes"])
        assert any(edge["source"] == str(customer.id) and edge["target"] == str(complaint.id) for edge in graph["edges"])
        assert any(relationship["type"] == "related_to" for relationship in graph["edges"] if relationship["source"] == str(complaint.id))
    finally:
        db.rollback()
        db.close()


def test_customer_risk_scores_repeat_complaints_high():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        customer, _ = setup_test_data(db)
        for i in range(2):
            complaint = Complaint(
                external_id=f"RISK-{uuid.uuid4()}",
                customer_id=customer.id,
                channel=Channel.EMAIL,
                raw_text="I am still waiting on my order.",
                created_at=datetime.utcnow() - timedelta(days=i + 2),
            )
            db.add(complaint)
            db.flush()
            db.add(ComplaintAnalysis(
                complaint_id=complaint.id,
                category="delivery",
                sentiment=Sentiment.NEGATIVE,
                sentiment_score=0.9,
                severity=Severity.HIGH,
                entities={"region": "Chennai"},
            ))
        db.commit()
        risk = CustomerRiskService().score_customer(db, customer.id)
        assert risk["risk_level"] in {"HIGH", "MEDIUM"}
        assert risk["reasons"]
    finally:
        db.rollback()
        db.close()


def test_decision_trace_persists_events():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        customer, complaint = setup_test_data(db)
        event = DecisionTraceService().record_event(db, complaint.id, "Intent detected", "UnderstandingAgent", "Address Change", 0.92)
        assert event.step == "Intent detected"
        trace = DecisionTraceService().get_trace(db, complaint.id)
        assert len(trace) == 1
        assert trace[0]["step"] == "Intent detected"
    finally:
        db.rollback()
        db.close()
