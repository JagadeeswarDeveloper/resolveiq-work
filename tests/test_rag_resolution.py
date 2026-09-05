"""Phase 3 retrieval and grounded resolution tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.resolution_agent import ResolutionAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.models import Base, Complaint, Customer, KnowledgeDocument, ResolutionRecommendation
from app.rag.chunking import chunk_document
from app.rag.ingestion import ingest_document
from app.rag.retriever import PolicyRetriever
from app.rag.service import ensure_demo_policies


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_policy_ingestion_and_metadata_retrieval(db):
    document = KnowledgeDocument(
        title="Delivery Policy",
        document_type="policy",
        category="delivery",
        version=2,
        source="Fictional internal policy",
        content="Late delivery: Orders more than two business days late qualify for a delivery fee waiver.\n\nEscalation: Escalate after two unsuccessful support contacts.",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = chunk_document(document.content)
    assert len(chunks) == 2
    await ingest_document(db, document)
    results = await PolicyRetriever().search(db, "late order delivery fee waiver", policy_type="policy")

    assert results
    assert results[0]["document"] == "Delivery Policy"
    assert results[0]["metadata"]["version"] == 2
    assert "delivery fee waiver" in results[0]["content"]


@pytest.mark.asyncio
async def test_resolution_contains_policy_evidence_and_missing_evidence_routes_to_review(db):
    await ensure_demo_policies(db)
    customer = Customer(name="RAG Customer", email="rag@example.com")
    db.add(customer)
    db.commit()
    db.refresh(customer)
    complaint = Complaint(customer_id=customer.id, channel="email", raw_text="My order is five days late and support has not helped.")
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # The normal resolution agent receives retrieved evidence and persists it.
    recommendation = await ResolutionAgent().generate_recommendation(db, complaint)
    assert recommendation.policy_evidence
    assert recommendation.policy_sources
    assert recommendation.policy_confidence >= 0
    db.delete(recommendation)
    db.commit()

    unsupported = ResolutionRecommendation(
        complaint_id=complaint.id,
        recommended_action="Apply an invented company benefit",
        customer_response="We will apply the benefit.",
        reasoning_summary="No evidence",
        confidence=0.9,
        policy_evidence=[],
        policy_confidence=0,
        requires_human_review=False,
    )
    db.add(unsupported)
    db.commit()
    decision = await SupervisorAgent().decide_routing(db, complaint)
    assert decision.decision.value == "HUMAN_APPROVAL"
    assert "missing_policy_evidence" in decision.guardrails_applied
