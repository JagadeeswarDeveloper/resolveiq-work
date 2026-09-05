import asyncio
import uuid
import pytest

from app.core.database import Base, SessionLocal, engine
from app.models import Channel, Customer, WorkflowEvent
from app.rag.service import ensure_demo_policies
from app.schemas import ComplaintCreate
from app.services.complaint_service import ComplaintService
from app.workflows import ComplaintGraph
from app.ai.llm.providers.fallback_provider import FallbackProvider
from app.ai.models import ComplaintUnderstanding, ResolutionRecommendation, SupervisorDecision


@pytest.mark.asyncio
async def test_demo_fallback_has_three_routing_paths():
    provider = FallbackProvider()
    scenarios = [
        ("FAQ: how do I reset my password?", "AUTO_RESOLVE"),
        ("I suspect fraud on my account", "ESCALATE"),
        ("My delivery is late and I need compensation", "HUMAN_APPROVAL"),
    ]
    for prompt, expected in scenarios:
        response = await provider.generate_structured(prompt, SupervisorDecision)
        assert response.data["decision"] == expected


@pytest.mark.asyncio
async def test_demo_fallback_understands_password_faq():
    provider = FallbackProvider()
    understanding = await provider.generate_structured(
        "COMPLAINT:\nHow do i reset my password?\n\nANALYSIS REQUIREMENTS:",
        ComplaintUnderstanding,
    )
    assert understanding.data["category"] == "account"
    assert understanding.data["urgency"] == "LOW"
    resolution = await provider.generate_structured(
        "COMPLAINT:\nHow do i reset my password?\n\nANALYSIS:\n- Category: account",
        ResolutionRecommendation,
    )
    assert resolution.data["compensation"] is None
    assert resolution.data["recommended_action"] == "Provide password reset instructions"


@pytest.mark.asyncio
async def test_canonical_graph_paths():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        await ensure_demo_policies(db)
        customer = Customer(name="Scenario Test", email=f"scenario-{uuid.uuid4().hex}@example.com")
        db.add(customer)
        db.commit()
        db.refresh(customer)
        graph = ComplaintGraph()
        scenarios = [
            ("FAQ: how do I reset my password?", "completed"),
            ("I've already contacted support twice. My order was supposed to arrive five days ago and nobody is helping me.", "pending_approval"),
            ("I suspect fraud on my account and need legal help.", "completed"),
        ]
        results = []
        for text, expected_status in scenarios:
            complaint = await ComplaintService().create_complaint(
                db, ComplaintCreate(customer_id=customer.id, channel=Channel.EMAIL, raw_text=text)
            )
            run = await graph.run(db, complaint.id)
            results.append(((run.state or {}).get("supervisor_decision", {}).get("decision"), run.status, complaint.id))
            assert run.status == expected_status
        assert [item[0] for item in results] == ["AUTO_RESOLVE", "HUMAN_APPROVAL", "ESCALATE"], results
    finally:
        db.close()


def test_workflow_pauses_and_resumes_without_duplicate_events():
    Base.metadata.create_all(bind=engine)

    async def exercise():
        db = SessionLocal()
        email = f"workflow-{uuid.uuid4().hex}@example.com"
        try:
            await ensure_demo_policies(db)
            customer = Customer(name="Graph Test", email=email)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            complaint = await ComplaintService().create_complaint(
                db,
                ComplaintCreate(
                    customer_id=customer.id,
                    channel=Channel.EMAIL,
                    raw_text="My order is five days late and I need compensation.",
                ),
            )
            graph = ComplaintGraph()
            run = await graph.run(db, complaint.id)
            assert run.status == "pending_approval"
            event_count = db.query(WorkflowEvent).filter(WorkflowEvent.workflow_id == run.id).count()
            resumed = await graph.resume(db, run.id, approved=True)
            assert resumed.status == "completed"
            assert resumed.current_node == "END"
            assert event_count == 7
            assert await graph.resume(db, run.id, approved=True) == resumed
        finally:
            db.close()

    asyncio.run(exercise())