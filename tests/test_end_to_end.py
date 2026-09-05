from fastapi.testclient import TestClient
import pytest

from app.core.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_complete_complaint_workflow_persists_arc_events():
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/complaints",
            json={
                "customer_email": "integration@example.com",
                "channel": "email",
                "raw_text": "My order is five days late and support has not helped.",
            },
        )
        assert created.status_code == 200
        complaint_id = created.json()["id"]

        for stage in ("analyze", "prioritize", "investigate", "resolve", "route"):
            response = client.post(f"/api/v1/complaints/{complaint_id}/{stage}")
            assert response.status_code == 200, response.text

        final = client.get(f"/api/v1/complaints/{complaint_id}")
        assert final.status_code == 200
        payload = final.json()
        assert payload["status"] in {"resolved", "pending_approval", "escalated"}
        assert {event["arc_stage"] for event in payload["arc_events"]} >= {
            "capture", "understand", "prioritize", "investigate", "reason", "resolve"
        }


def test_demo_workflow_is_repeatable():
    with TestClient(app) as client:
        first = client.post("/api/v1/complaints/demo")
        second = client.post("/api/v1/complaints/demo")
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] == second.json()["id"]
