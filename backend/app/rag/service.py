"""RAG application service and fictional demo policies."""

from sqlalchemy.orm import Session

from app.models import KnowledgeDocument
from app.rag.ingestion import ingest_document
from app.rag.retriever import PolicyRetriever

DEMO_POLICIES = [
    ("Account & Password Support Policy", "policy", "account", "Customers can reset a forgotten password through the secure account recovery link. Support must not request or reveal the customer's password."),
    ("Delivery SLA & Late Delivery Policy", "policy", "delivery", "Orders are expected within 5-7 business days. When an order is more than two business days late, support may offer expedited replacement and waive the delivery fee. The customer must be told the revised delivery estimate."),
    ("Refund & Compensation Policy", "policy", "compensation", "A confirmed delivery failure qualifies for a delivery fee waiver and a service credit of up to $20. Refunds require confirmation that the order cannot be delivered or that the customer requests cancellation."),
    ("Customer Escalation Policy", "policy", "escalation", "Escalate complaints after two unsuccessful support contacts, or when a promised delivery date has passed and the customer remains without a resolution. Human approval is required for compensation above $100."),
    ("Subscription Support Policy", "policy", "subscription", "Subscription changes take effect at the next billing boundary unless a billing error is confirmed. Support must explain the effective date before making a change."),
    ("Product Replacement Policy", "policy", "replacement", "A defective or unusable product may be replaced after basic troubleshooting. If replacement stock is unavailable, offer a refund according to the Refund & Compensation Policy."),
]


async def ensure_demo_policies(db: Session) -> None:
    for title, document_type, category, content in DEMO_POLICIES:
        document = db.query(KnowledgeDocument).filter(KnowledgeDocument.title == title).first()
        if not document:
            document = KnowledgeDocument(title=title, document_type=document_type, category=category, content=content, status="draft", source="ResolveIQ fictional demo policy")
            db.add(document)
            db.commit()
            db.refresh(document)
        if not document.chunks:
            await ingest_document(db, document)


async def retrieve_policy_evidence(db: Session, query: str, limit: int = 5) -> list[dict]:
    return await PolicyRetriever().search(db, query, limit=limit)
