"""Populate a rich, repeatable synthetic dataset for local ResolveIQ demos."""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine
from app.models import (
    ARCStage,
    Channel,
    Complaint,
    ComplaintAnalysis,
    ComplaintCluster,
    ComplaintEvent,
    ComplaintPriority,
    ComplaintStatus,
    Customer,
    Incident,
    IncidentEvidence,
    IncidentStatus,
    KnowledgeChunk,
    KnowledgeDocument,
    PriorityLevel,
    ResolutionRecommendation,
    Sentiment,
    Severity,
    SupervisorDecision,
    cluster_complaints,
    incident_complaints,
)


SEED_MARKER = "DEMO-CUST-001"
RANDOM = random.Random(42)
NOW = datetime.utcnow()

CUSTOMER_NAMES = [
    "Avery Morgan", "Jordan Patel", "Sam Rivera", "Taylor Brooks",
    "Casey Nguyen", "Riley Chen", "Morgan Ellis", "Jamie Okafor",
    "Drew Wilson", "Quinn Carter", "Alexis Reed", "Cameron Bell",
    "Parker Shah", "Reese Martin", "Skyler Kim", "Rowan Davis",
    "Emerson Clark", "Finley Ross", "Sage Thompson", "Kendall Young",
    "Harper Lewis", "Blair Adams", "Milan Foster", "Devon Wright",
]

ISSUES = [
    ("delivery", "late_delivery", "The order is late and the customer needs a clear delivery update.", "delivery delay"),
    ("delivery", "missing_package", "The package was marked delivered but the customer cannot locate it.", "missing package"),
    ("billing", "duplicate_charge", "The customer reports being charged twice for one purchase.", "duplicate charge"),
    ("billing", "unexpected_fee", "The customer disputes an unexpected fee on the latest invoice.", "unexpected fee"),
    ("refund", "refund_delay", "The requested refund has not appeared within the promised window.", "refund delay"),
    ("technical", "checkout_error", "The customer cannot complete checkout because of a recurring error.", "checkout failure"),
    ("technical", "device_setup", "The customer needs help setting up a recently purchased device.", "setup assistance"),
    ("account", "access_locked", "The customer is locked out and cannot regain account access.", "account access"),
    ("product", "damaged_item", "The item arrived damaged and the customer requests a replacement.", "damaged product"),
    ("subscription", "cancellation", "The customer requested cancellation but billing continued.", "subscription cancellation"),
]

DOCUMENT_TOPICS = [
    ("Delivery Recovery Policy", "delivery", "Late delivery cases should receive a carrier investigation, a verified ETA, and proactive customer communication."),
    ("Missing Package Runbook", "delivery", "For delivered-but-missing packages, verify address details, carrier scan data, and open a claim before issuing replacement guidance."),
    ("Refund Service Levels", "refund", "Standard refunds should be acknowledged within one business day and completed within five to seven business days."),
    ("Duplicate Charge Procedure", "billing", "Duplicate charges require payment ledger verification, reversal of the duplicate transaction, and a written confirmation."),
    ("Checkout Incident Playbook", "technical", "Repeated checkout errors should be grouped by release, browser, region, and payment method before escalation."),
    ("Account Recovery Standard", "account", "Identity verification is required before account recovery. Never disclose security answers or reset links to an unverified requester."),
    ("Damaged Product Replacement", "product", "Photographic evidence is preferred for damage claims. Offer replacement or refund according to inventory and customer preference."),
    ("Subscription Cancellation Controls", "subscription", "Cancellation requests must stop future renewals and provide a confirmation reference to the customer."),
    ("High Value Customer Handling", "service", "Platinum customers receive priority review, a named owner, and a same-day first response when service is disrupted."),
    ("Escalation and Human Approval", "governance", "Legal, safety, fraud, regulatory, and high-compensation cases require human review before resolution."),
    ("Customer Communication Tone Guide", "service", "Acknowledge impact, state what is known, give a concrete next step, and avoid promises that depend on unverified information."),
    ("SLA Breach Response", "governance", "SLA breaches should be logged, explained to the customer, and reviewed for a service credit when policy permits."),
    ("Payment Dispute Evidence", "billing", "Payment disputes should include transaction IDs, timestamps, order references, and the exact amount under review."),
    ("Regional Carrier Exceptions", "delivery", "Weather and regional carrier disruptions require location-aware ETAs and a follow-up task rather than generic messaging."),
    ("Replacement Inventory Rules", "product", "Replacement promises must be checked against available inventory and shipping constraints before confirmation."),
    ("Privacy Request Handling", "account", "Privacy requests require identity verification, a documented request type, and the applicable response deadline."),
    ("Support Handoff Checklist", "service", "A handoff must include the complaint summary, customer impact, prior actions, owner, and next promised update."),
    ("Incident Detection Signals", "governance", "A rising complaint cluster is stronger evidence of an incident when category, product, region, and time window align."),
]


def make_customer(index: int) -> Customer:
    tier = "platinum" if index % 9 == 0 else "gold" if index % 3 == 0 else "standard"
    return Customer(
        external_id=f"DEMO-CUST-{index:03d}",
        name=CUSTOMER_NAMES[index - 1],
        email=f"demo.customer{index:03d}@resolveiq.local",
        phone=f"+1-555-01{index:03d}",
        tier=tier,
        account_status="active" if index % 17 else "suspended",
        lifetime_value=round(850 + index * 437.5, 2),
        complaints_count=5,
    )


def seed_documents(db):
    documents = []
    for index, (title, category, policy) in enumerate(DOCUMENT_TOPICS, 1):
        existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.title == f"Demo {title}").first()
        if existing:
            documents.append(existing)
            continue
        document = KnowledgeDocument(
            title=f"Demo {title}",
            description=f"Synthetic policy reference for {category} workflows.",
            content=f"{policy}\n\nOperational note: This fictional policy is included to make the local ResolveIQ demo searchable and reviewable.",
            document_type="policy" if index % 3 else "runbook",
            category=category,
            version=1,
            is_active=True,
            status="published",
            source="ResolveIQ synthetic demo dataset",
            created_at=NOW - timedelta(days=90 - index),
            updated_at=NOW - timedelta(days=index),
        )
        db.add(document)
        db.flush()
        for chunk_index in range(1, 4):
            db.add(KnowledgeChunk(
                document_id=document.id,
                chunk_index=chunk_index,
                content=f"{title}, section {chunk_index}: {policy} Apply this guidance with customer-specific facts and human approval guardrails.",
                embedding=[round((index + chunk_index + offset) / 100, 4) for offset in range(8)],
                chunk_metadata={"source": "synthetic_demo", "section": chunk_index},
            ))
        documents.append(document)
    return documents


def seed_customers(db):
    customers = []
    for index in range(1, 25):
        customer = db.query(Customer).filter(Customer.external_id == f"DEMO-CUST-{index:03d}").first()
        if not customer:
            customer = make_customer(index)
            db.add(customer)
            db.flush()
        customers.append(customer)
    return customers


def seed_complaints(db, customers):
    complaints = []
    for index in range(1, 121):
        customer = customers[(index - 1) % len(customers)]
        category, subcategory, summary, issue_label = ISSUES[(index - 1) % len(ISSUES)]
        status_cycle = [ComplaintStatus.RESOLVED, ComplaintStatus.PENDING_APPROVAL, ComplaintStatus.INVESTIGATING, ComplaintStatus.RESOLUTION_PROPOSED, ComplaintStatus.ESCALATED, ComplaintStatus.CLOSED]
        status = status_cycle[(index - 1) % len(status_cycle)]
        created_at = NOW - timedelta(days=(index * 2) % 45, hours=index % 12)
        complaint = db.query(Complaint).filter(Complaint.external_id == f"DEMO-CMP-{index:04d}").first()
        if complaint:
            complaints.append(complaint)
            continue
        complaint = Complaint(
            external_id=f"DEMO-CMP-{index:04d}",
            customer_id=customer.id,
            channel=list(Channel)[(index - 1) % len(Channel)],
            raw_text=f"I need help with my order. This is a {issue_label} problem. {summary} Please tell me what happens next and when I should expect an update.",
            normalized_text=f"Customer reports {issue_label}.",
            status=status,
            language="en",
            created_at=created_at,
            updated_at=created_at + timedelta(hours=2),
            resolved_at=created_at + timedelta(hours=18) if status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED] else None,
        )
        db.add(complaint)
        db.flush()
        sentiment = Sentiment.HIGHLY_NEGATIVE if index % 11 == 0 else Sentiment.NEGATIVE if index % 4 == 0 else Sentiment.NEUTRAL
        severity = Severity.CRITICAL if index % 23 == 0 else Severity.HIGH if index % 7 == 0 else Severity.MEDIUM
        score = min(99, 42 + (18 if sentiment == Sentiment.NEGATIVE else 0) + (28 if severity == Severity.HIGH else 40 if severity == Severity.CRITICAL else 0) + (12 if customer.tier == "platinum" else 0))
        priority_level = PriorityLevel.CRITICAL if score >= 85 else PriorityLevel.HIGH if score >= 65 else PriorityLevel.MEDIUM
        db.add(ComplaintAnalysis(
            complaint_id=complaint.id,
            category=category,
            subcategory=subcategory,
            intent=f"Resolve {issue_label}",
            sentiment=sentiment,
            sentiment_score=round(0.55 + (index % 40) / 100, 2),
            severity=severity,
            entities={"product": ["Aster laptop", "Nimbus router", "Orbit subscription"][(index - 1) % 3], "order_id": f"ORD-{index:05d}", "region": ["North America", "Europe", "APAC"][(index - 1) % 3]},
            summary=summary,
            key_issues=[issue_label, "customer_impact"],
            analysis_metadata={"source": "synthetic_demo", "confidence": round(0.72 + (index % 20) / 100, 2)},
            created_at=created_at + timedelta(minutes=3),
        ))
        db.add(ComplaintPriority(
            complaint_id=complaint.id,
            priority_score=score,
            priority_level=priority_level,
            severity_factor=0.35 if severity in [Severity.HIGH, Severity.CRITICAL] else 0.15,
            sentiment_factor=0.3 if sentiment in [Sentiment.NEGATIVE, Sentiment.HIGHLY_NEGATIVE] else 0.1,
            sla_breach_factor=0.25 if index % 5 == 0 else 0.0,
            customer_value_factor=0.3 if customer.tier == "platinum" else 0.15,
            repeat_complaint_factor=0.2,
            incident_linkage_factor=0.15 if index % 3 == 0 else 0.0,
            sla_breached=index % 5 == 0,
            sla_response_time=30 + (index % 8) * 15,
            sla_resolution_time=360 + (index % 12) * 60,
            reasons=[f"{severity.value} severity", f"{sentiment.value} sentiment", "Repeat customer pattern"],
            created_at=created_at + timedelta(minutes=5),
        ))
        action_by_category = {
            "delivery": "Open a carrier investigation, provide a verified delivery estimate, and offer expedited replacement if the package is confirmed lost.",
            "billing": "Verify the payment ledger, reverse any duplicate or incorrect charge, and send a written transaction confirmation.",
            "refund": "Confirm refund eligibility, submit the refund request, and provide the expected settlement window to the customer.",
            "technical": "Reproduce the technical issue, capture environment details, and route a fix or workaround to the owning engineering team.",
            "account": "Verify identity through a trusted channel, secure the account, review recent changes, and restore access only after security checks.",
            "product": "Document the product damage, verify replacement inventory, and arrange a replacement or refund based on customer preference.",
            "subscription": "Stop future renewal, verify the cancellation effective date, and correct any billing caused by the cancellation failure.",
        }
        action = action_by_category.get(category, "Assign an owner, investigate the complaint, and provide a verified next step within one business day.")
        recommendation = ResolutionRecommendation(
            complaint_id=complaint.id,
            recommended_action=action,
            customer_response=f"We are sorry about the {issue_label}. We have assigned this to a specialist and will provide a confirmed next step within one business day.",
            internal_actions=["Verify order and account history", "Check applicable policy", "Assign accountable owner", "Send follow-up update"],
            compensation={"type": "service_credit" if index % 2 else "refund", "amount": 25 + (index % 4) * 25, "reason": "Service recovery recommendation"},
            reasoning_summary=f"Recommendation is based on the {category} category, the reported {issue_label}, customer impact, and the {severity.value} severity assessment.",
            policy_sources=[f"Demo {DOCUMENT_TOPICS[(index - 1) % len(DOCUMENT_TOPICS)][0]}"],
            policy_evidence=[{"document": "Synthetic policy", "section": "service recovery", "content": summary, "score": 0.84}],
            policy_confidence=0.84,
            confidence=round(0.74 + (index % 20) / 100, 2),
            requires_human_review=index % 6 == 0 or severity == Severity.CRITICAL,
            created_at=created_at + timedelta(minutes=8),
        )
        db.add(recommendation)
        decision = "ESCALATE" if severity == Severity.CRITICAL else "HUMAN_APPROVAL" if recommendation.requires_human_review else "AUTO_RESOLVE"
        db.add(SupervisorDecision(
            complaint_id=complaint.id,
            decision=decision,
            reasoning="Synthetic demo routing based on severity, policy evidence, and compensation guardrails.",
            confidence=0.91 if decision != "AUTO_RESOLVE" else 0.86,
            guardrails_applied=["critical_priority"] if severity == Severity.CRITICAL else ["requires_human_review"] if recommendation.requires_human_review else [],
            risk_factors=[issue_label, "sla_breach"] if index % 5 == 0 else [issue_label],
            escalation_reason="Critical severity requires human ownership" if decision == "ESCALATE" else None,
            created_at=created_at + timedelta(minutes=10),
        ))
        for stage in [ARCStage.CAPTURE, ARCStage.UNIFY, ARCStage.UNDERSTAND, ARCStage.PRIORITIZE, ARCStage.INVESTIGATE, ARCStage.REASON, ARCStage.RESOLVE]:
            db.add(ComplaintEvent(
                complaint_id=complaint.id,
                arc_stage=stage,
                agent_name="SyntheticDemoSeeder" if stage == ARCStage.CAPTURE else "ResolveIQ Demo Agent",
                status="completed",
                input_reference={"source": "synthetic_demo"},
                output_reference={"stage": stage.value, "category": category},
                duration=120 + index,
                timestamp=created_at + timedelta(minutes=stage.value.__len__()),
            ))
        complaints.append(complaint)
    return complaints


def seed_clusters_and_incidents(db, complaints):
    clusters = []
    incident_link_columns = {column["name"] for column in inspect(engine).get_columns("incident_complaints")}
    for index in range(1, 9):
        category, _, _, _ = ISSUES[(index - 1) % len(ISSUES)]
        cluster = db.query(ComplaintCluster).filter(ComplaintCluster.name == f"Demo Cluster {index:02d}").first()
        if not cluster:
            cluster = ComplaintCluster(
                name=f"Demo Cluster {index:02d}",
                description=f"Synthetic cluster of recurring {category} complaints across a recent time window.",
                category=category,
                status="confirmed" if index % 3 else "investigating",
                cluster_score=round(0.71 + index / 100, 2),
                complaint_count=15,
                first_detected_at=NOW - timedelta(days=30 - index),
                last_updated_at=NOW - timedelta(hours=index),
                affected_region=["North America", "Europe", "APAC"][index % 3],
                affected_product=["Aster laptop", "Nimbus router", "Orbit subscription"][index % 3],
                severity="high" if index % 3 == 0 else "medium",
                confidence=round(0.78 + index / 100, 2),
            )
            db.add(cluster)
            db.flush()
        clusters.append(cluster)
        cluster_complaint_rows = []
        selected = complaints[(index - 1) * 15:index * 15]
        for complaint in selected:
            cluster_complaint_rows.append({"cluster_id": cluster.id, "complaint_id": complaint.id, "relationship_score": round(0.72 + (complaint.id.int % 20) / 100, 2), "relationship_reason": {"signals": ["category", "time_window", "product"]}})
        if cluster_complaint_rows:
            db.execute(cluster_complaints.insert().prefix_with("OR IGNORE"), cluster_complaint_rows)

        incident = db.query(Incident).filter(Incident.external_id == f"DEMO-INC-{index:03d}").first()
        if not incident:
            incident = Incident(
                external_id=f"DEMO-INC-{index:03d}",
                title=f"{category.title()} disruption wave {index}",
                description=f"Synthetic operational incident showing a rising pattern of {category} complaints.",
                status=[IncidentStatus.DETECTED, IncidentStatus.INVESTIGATING, IncidentStatus.CONFIRMED, IncidentStatus.RESOLVING][index % 4],
                detected_at=NOW - timedelta(days=18 - index),
                detected_by_agent="IncidentDetectionAgent",
                affected_products=[cluster.affected_product],
                affected_regions=[cluster.affected_region],
                affected_customers_count=15,
                complaint_count=15,
                evidence={"signals": ["volume_spike", "semantic_similarity", "shared_product"], "sample_size": 15},
                confidence=cluster.confidence,
                suspected_root_cause=f"Likely {category} process degradation under investigation.",
                potential_root_cause=f"Shared {category} workflow or partner dependency.",
                evidence_summary="Complaint volume and shared attributes exceed the synthetic detection threshold.",
                severity="high" if index % 3 == 0 else "medium",
                high_priority_count=5 + index,
                sla_breach_count=2 + index % 5,
                estimated_business_impact=round(12000 + index * 1875.5, 2),
                regions_affected=1 + index % 3,
                products_affected=1 + index % 2,
                baseline_volume=4.0 + index,
                current_volume=15,
                volume_change_percent=round(120 + index * 11.5, 1),
                cluster_id=cluster.id,
                trend="increasing" if index % 4 else "stable",
                first_complaint_at=NOW - timedelta(days=20 - index),
                last_complaint_at=NOW - timedelta(hours=index),
                created_at=NOW - timedelta(days=18 - index),
                updated_at=NOW - timedelta(hours=index),
            )
            db.add(incident)
            db.flush()
            incident_links = [{"incident_id": incident.id, "complaint_id": complaint.id} for complaint in selected]
            if "relationship_score" in incident_link_columns:
                for link in incident_links:
                    link["relationship_score"] = 0.8
                    link["relationship_reason"] = {"signals": ["cluster_match"]}
            db.execute(incident_complaints.insert().prefix_with("OR IGNORE"), incident_links)
            db.add(IncidentEvidence(
                incident_id=incident.id,
                cluster_id=cluster.id,
                detection_timestamp=incident.detected_at,
                complaint_ids=[str(complaint.id) for complaint in selected[:8]],
                similarity_scores=[0.81, 0.84, 0.87, 0.79],
                signals_used=["volume_spike", "category_match", "product_match", "region_match"],
                thresholds={"minimum_cluster_size": 5, "volume_change_percent": 50},
                ai_assessment={"summary": incident.evidence_summary, "confidence": incident.confidence},
                confidence=incident.confidence,
                recommended_actions=["Assign incident owner", "Contact affected customers", "Review partner performance"],
            ))
    return clusters


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Customer).filter(Customer.external_id == SEED_MARKER).first():
            print("Demo dataset already exists. No changes made.")
            return
        documents = seed_documents(db)
        customers = seed_customers(db)
        complaints = seed_complaints(db, customers)
        clusters = seed_clusters_and_incidents(db, complaints)
        db.commit()
        print(f"Seeded {len(customers)} customers, {len(complaints)} complaints, {len(documents)} documents, {len(clusters)} clusters, and 8 incidents.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
