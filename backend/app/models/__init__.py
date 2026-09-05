"""SQLAlchemy ORM models for ResolveIQ."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
    Index,
    CheckConstraint,
    TypeDecorator,
)
from sqlalchemy.orm import relationship

JSONB = JSON


class UUIDType(TypeDecorator):
    """Cross-database UUID type compatible with SQLite and PostgreSQL."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return UUID(as_uuid=True)
        return String(36)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)

from app.core.database import Base


# ============================================================================
# Enums
# ============================================================================


class Channel(str, Enum):
    """Complaint channel source."""

    EMAIL = "email"
    TICKET = "ticket"
    WEB_FORM = "web_form"
    CHAT = "chat"
    PHONE = "phone"
    SOCIAL_MEDIA = "social_media"


class ComplaintStatus(str, Enum):
    """Complaint lifecycle status."""

    RECEIVED = "received"
    NORMALIZED = "normalized"
    CLASSIFIED = "classified"
    PRIORITIZED = "prioritized"
    INVESTIGATING = "investigating"
    RESOLUTION_PROPOSED = "resolution_proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    REJECTED = "rejected"
    CLOSED = "closed"


class ARCStage(str, Enum):
    """ARC lifecycle stages."""

    CAPTURE = "capture"
    UNIFY = "unify"
    UNDERSTAND = "understand"
    PRIORITIZE = "prioritize"
    INVESTIGATE = "investigate"
    REASON = "reason"
    RESOLVE = "resolve"
    LEARN = "learn"


class Sentiment(str, Enum):
    """Sentiment classification."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    HIGHLY_NEGATIVE = "highly_negative"


class Severity(str, Enum):
    """Complaint severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PriorityLevel(str, Enum):
    """Priority level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status."""

    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ============================================================================
# Domain Models
# ============================================================================


class Customer(Base):
    """Customer profile."""

    __tablename__ = "customers"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20))
    tier = Column(String(50), default="standard")  # standard, gold, platinum
    account_status = Column(String(50), default="active")  # active, suspended, closed
    lifetime_value = Column(Float, default=0.0)
    complaints_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="customer")
    complaints = relationship("Complaint", back_populates="customer")

    __table_args__ = (
        Index("idx_customer_tier", "tier"),
        Index("idx_customer_account_status", "account_status"),
    )


class Order(Base):
    """Customer order."""

    __tablename__ = "orders"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, index=True)
    customer_id = Column(UUIDType(), ForeignKey("customers.id"), nullable=False)
    product = Column(String(255), nullable=False)
    product_category = Column(String(100))
    order_date = Column(DateTime, nullable=False)
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, shipped, delivered, cancelled
    shipping_address = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    complaints = relationship("Complaint", secondary="complaint_orders")

    __table_args__ = (
        Index("idx_order_customer_id", "customer_id"),
        Index("idx_order_external_id", "external_id"),
        Index("idx_order_status", "status"),
    )


class Complaint(Base):
    """Main complaint/ticket record."""

    __tablename__ = "complaints"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, index=True)
    customer_id = Column(UUIDType(), ForeignKey("customers.id"), nullable=False)
    channel = Column(SQLEnum(Channel), nullable=False)
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text)
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.RECEIVED, index=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Relationships
    customer = relationship("Customer", back_populates="complaints")
    analysis = relationship("ComplaintAnalysis", back_populates="complaint", uselist=False)
    priority = relationship("ComplaintPriority", back_populates="complaint", uselist=False)
    resolution_recommendation = relationship(
        "ResolutionRecommendation",
        primaryjoin="Complaint.id==ResolutionRecommendation.complaint_id",
        uselist=False,
        viewonly=True,
    )
    arc_events = relationship("ComplaintEvent", back_populates="complaint", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="complaint", cascade="all, delete-orphan")
    related_complaints = relationship(
        "Complaint",
        secondary="complaint_relations",
        primaryjoin="Complaint.id==complaint_relations.c.source_complaint_id",
        secondaryjoin="Complaint.id==complaint_relations.c.related_complaint_id",
    )

    __table_args__ = (
        Index("idx_complaint_customer_id", "customer_id"),
        Index("idx_complaint_status", "status"),
        Index("idx_complaint_channel", "channel"),
        Index("idx_complaint_created_at", "created_at"),
    )


class ComplaintAnalysis(Base):
    """AI-generated analysis of a complaint."""

    __tablename__ = "complaint_analysis"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False, unique=True)
    
    # Classification
    category = Column(String(100))  # delivery, billing, refund, account, technical, etc.
    subcategory = Column(String(100))
    intent = Column(String(255))

    # Sentiment
    sentiment = Column(SQLEnum(Sentiment), default=Sentiment.NEUTRAL)
    sentiment_score = Column(Float)  # 0.0-1.0

    # Severity (problem severity, not priority)
    severity = Column(SQLEnum(Severity), default=Severity.MEDIUM)

    # Entities extraction
    entities = Column(JSONB)  # {"product": "...", "order_id": "...", "location": "..."}
    
    # Summary
    summary = Column(Text)
    key_issues = Column(JSONB)  # List of identified issues

    analysis_metadata = Column(JSONB)  # Additional analysis metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    complaint = relationship("Complaint", back_populates="analysis")

    __table_args__ = (
        Index("idx_analysis_category", "category"),
        Index("idx_analysis_sentiment", "sentiment"),
    )


class ComplaintPriority(Base):
    """Priority assessment for complaint."""

    __tablename__ = "complaint_priority"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False, unique=True)
    
    priority_score = Column(Integer)  # 0-100
    priority_level = Column(SQLEnum(PriorityLevel))
    
    # Contributing factors
    severity_factor = Column(Float)
    sentiment_factor = Column(Float)
    sla_breach_factor = Column(Float)
    customer_value_factor = Column(Float)
    repeat_complaint_factor = Column(Float)
    incident_linkage_factor = Column(Float)
    
    # SLA Tracking
    sla_breached = Column(Boolean, default=False)
    sla_response_time = Column(Integer)  # minutes
    sla_resolution_time = Column(Integer)  # minutes
    
    # Reasons
    reasons = Column(JSONB)  # List of reason strings
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    complaint = relationship("Complaint", back_populates="priority")

    __table_args__ = (
        Index("idx_priority_level", "priority_level"),
        Index("idx_priority_sla_breached", "sla_breached"),
    )


class ComplaintEvent(Base):
    """ARC lifecycle event for complaint."""

    __tablename__ = "complaint_events"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False)
    
    arc_stage = Column(SQLEnum(ARCStage), nullable=False)
    agent_name = Column(String(255))  # Name of agent that handled this stage
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    
    input_reference = Column(JSONB)  # Reference to input data
    output_reference = Column(JSONB)  # Reference to output data
    
    duration = Column(Integer)  # milliseconds
    error = Column(Text)  # Error message if failed
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    complaint = relationship("Complaint", back_populates="arc_events")

    __table_args__ = (
        Index("idx_event_arc_stage", "arc_stage"),
        Index("idx_event_complaint_id", "complaint_id"),
        Index("idx_event_timestamp", "timestamp"),
    )


class ResolutionRecommendation(Base):
    """Recommended resolution for complaint."""

    __tablename__ = "resolution_recommendations"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False)
    
    recommended_action = Column(Text, nullable=False)
    customer_response = Column(Text)  # What to say to customer
    internal_actions = Column(JSONB)  # List of internal actions
    compensation = Column(JSONB)  # {"type": "refund", "amount": 100, "reason": "..."}
    
    reasoning_summary = Column(Text)
    policy_sources = Column(JSONB)  # References to used policies
    policy_evidence = Column(JSONB)  # Concise retrieved evidence
    policy_confidence = Column(Float, default=0.0)
    confidence = Column(Float)  # 0.0-1.0
    
    requires_human_review = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_recommendation_complaint_id", "complaint_id"),
    )


class SupervisorDecision(Base):
    """Supervisor agent routing decision."""

    __tablename__ = "supervisor_decisions"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False)
    
    decision = Column(String(50), nullable=False)  # AUTO_RESOLVE, HUMAN_APPROVAL, ESCALATE
    reasoning = Column(Text, nullable=False)
    confidence = Column(Float)  # 0.0-1.0
    
    guardrails_applied = Column(JSONB)  # List of guardrails triggered
    risk_factors = Column(JSONB)  # List of risk factors identified
    escalation_reason = Column(Text)  # Why escalated if decision is ESCALATE
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_supervisor_decision_complaint_id", "complaint_id"),
        Index("idx_supervisor_decision_decision", "decision"),
    )


class Incident(Base):
    """Operational incident (multiple related complaints)."""

    __tablename__ = "incidents"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.DETECTED, index=True)
    
    # Detection info
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    detected_by_agent = Column(String(255))  # Name of detecting agent
    
    # Scope
    affected_products = Column(JSONB)  # List
    affected_regions = Column(JSONB)  # List
    affected_customers_count = Column(Integer, default=0)
    complaint_count = Column(Integer, default=0)
    
    # Evidence
    evidence = Column(JSONB)  # Supporting evidence
    confidence = Column(Float)  # 0.0-1.0
    suspected_root_cause = Column(Text)
    potential_root_cause = Column(Text)
    evidence_summary = Column(Text)
    severity = Column(String(50), default="medium")
    high_priority_count = Column(Integer, default=0)
    sla_breach_count = Column(Integer, default=0)
    estimated_business_impact = Column(Float, default=0.0)
    regions_affected = Column(Integer, default=0)
    products_affected = Column(Integer, default=0)
    baseline_volume = Column(Float, default=0.0)
    current_volume = Column(Integer, default=0)
    volume_change_percent = Column(Float, default=0.0)
    cluster_id = Column(UUIDType(), ForeignKey("complaint_clusters.id"))
    
    # Trend
    trend = Column(String(50))  # increasing, stable, decreasing
    first_complaint_at = Column(DateTime)
    last_complaint_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    complaints = relationship(
        "Complaint",
        secondary="incident_complaints",
        back_populates="incidents",
    )
    cluster = relationship("ComplaintCluster", back_populates="incidents")

    __table_args__ = (
        Index("idx_incident_status", "status"),
        Index("idx_incident_detected_at", "detected_at"),
    )


class KnowledgeDocument(Base):
    """Knowledge base document."""

    __tablename__ = "knowledge_documents"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    document_type = Column(String(100))  # policy, faq, sop, runbook, etc.
    status = Column(String(50), default="draft")
    source = Column(String(255), default="ResolveIQ demo policy")
    category = Column(String(100))  # delivery, billing, etc.
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_doc_type", "document_type"),
        Index("idx_doc_category", "category"),
        Index("idx_doc_active", "is_active"),
    )


class KnowledgeChunk(Base):
    """Chunked segment of knowledge document for RAG."""

    __tablename__ = "knowledge_chunks"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUIDType(), ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)
    embedding = Column(JSONB)  # Vector embedding (or use pgvector extension)
    chunk_metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunk_document_id", "document_id"),
    )


class AuditLog(Base):
    """Audit trail for all meaningful actions."""

    __tablename__ = "audit_logs"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent_name = Column(String(255))  # Agent or system that performed action
    action = Column(String(255), nullable=False)  # analyze, prioritize, escalate, etc.
    
    input_summary = Column(JSONB)
    output_summary = Column(JSONB)
    
    model_used = Column(String(255))
    model_version = Column(String(50))
    
    retrieved_sources = Column(JSONB)  # Knowledge sources used
    decision = Column(String(255))
    latency_ms = Column(Integer)
    status = Column(String(50), default="success")  # success, error, partial
    error_message = Column(Text)

    # Relationships
    complaint = relationship("Complaint", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_complaint_id", "complaint_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_agent", "agent_name"),
    )


class AgentExecution(Base):
    """Execution record for agent operations."""

    __tablename__ = "agent_executions"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False)
    
    agent_name = Column(String(255), nullable=False)  # Name of agent
    arc_stage = Column(SQLEnum(ARCStage), nullable=False)  # Which ARC stage
    
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    model_used = Column(String(255))  # Which LLM model
    tokens_used = Column(Integer)
    
    input_summary = Column(JSONB)  # Summarized input (no secrets)
    output_summary = Column(JSONB)  # Summarized output
    
    latency_ms = Column(Integer)  # Execution time
    error_message = Column(Text)  # If failed
    
    is_demo_mode = Column(Boolean, default=False)  # Was this with fallback provider

    __table_args__ = (
        Index("idx_agent_execution_complaint_id", "complaint_id"),
        Index("idx_agent_execution_agent_name", "agent_name"),
        Index("idx_agent_execution_status", "status"),
        Index("idx_agent_execution_started_at", "started_at"),
    )


class WorkflowRun(Base):
    """Durable checkpoint for an orchestrated complaint workflow."""

    __tablename__ = "workflow_runs"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False, index=True)
    status = Column(String(50), default="running", nullable=False, index=True)
    current_node = Column(String(50), default="CAPTURE", nullable=False)
    state = Column(JSONB, default=dict)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_workflow_run_complaint_status", "complaint_id", "status"),
    )


class WorkflowEvent(Base):
    """Auditable node transition with an idempotency key."""

    __tablename__ = "workflow_events"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUIDType(), ForeignKey("workflow_runs.id"), nullable=False, index=True)
    complaint_id = Column(UUIDType(), ForeignKey("complaints.id"), nullable=False, index=True)
    node = Column(String(50), nullable=False)
    arc_stage = Column(SQLEnum(ARCStage), nullable=False)
    agent_or_tool = Column(String(255))
    status = Column(String(50), default="completed", nullable=False)
    duration_ms = Column(Integer)
    output_summary = Column(JSONB)
    error = Column(Text)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ComplaintCluster(Base):
    """Candidate group of complaints with shared semantic context."""

    __tablename__ = "complaint_clusters"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    status = Column(String(50), default="candidate", index=True)
    cluster_score = Column(Float, default=0.0)
    complaint_count = Column(Integer, default=0)
    first_detected_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    affected_region = Column(String(255))
    affected_product = Column(String(255))
    severity = Column(String(50), default="medium")
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incidents = relationship("Incident", back_populates="cluster")


class IncidentEvidence(Base):
    """Immutable-ish audit record for one detection run and its signals."""

    __tablename__ = "incident_evidence"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUIDType(), ForeignKey("incidents.id"), nullable=False, index=True)
    cluster_id = Column(UUIDType(), ForeignKey("complaint_clusters.id"))
    detection_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    complaint_ids = Column(JSONB)
    similarity_scores = Column(JSONB)
    signals_used = Column(JSONB)
    thresholds = Column(JSONB)
    ai_assessment = Column(JSONB)
    confidence = Column(Float)
    recommended_actions = Column(JSONB)


# ============================================================================
# Association Tables
# ============================================================================


def get_complaint_orders_table():
    """Association table for complaints and orders."""
    from sqlalchemy import Table, Column, ForeignKey, UUID as SQLUUID
    return Table(
        "complaint_orders",
        Base.metadata,
        Column("complaint_id", UUIDType(), ForeignKey("complaints.id"), primary_key=True),
        Column("order_id", UUIDType(), ForeignKey("orders.id"), primary_key=True),
    )


def get_complaint_relations_table():
    """Association table for related complaints."""
    from sqlalchemy import Table, Column, ForeignKey, UUID as SQLUUID
    return Table(
        "complaint_relations",
        Base.metadata,
        Column("source_complaint_id", UUIDType(), ForeignKey("complaints.id"), primary_key=True),
        Column("related_complaint_id", UUIDType(), ForeignKey("complaints.id"), primary_key=True),
    )


def get_cluster_complaints_table():
    """Association table for scored complaint clusters."""
    from sqlalchemy import Table, Column, ForeignKey
    return Table(
        "cluster_complaints",
        Base.metadata,
        Column("cluster_id", UUIDType(), ForeignKey("complaint_clusters.id"), primary_key=True),
        Column("complaint_id", UUIDType(), ForeignKey("complaints.id"), primary_key=True),
        Column("relationship_score", Float),
        Column("relationship_reason", JSONB),
    )


def get_incident_complaints_table():
    """Association table for incidents and complaints."""
    from sqlalchemy import Table, Column, ForeignKey, UUID as SQLUUID
    return Table(
        "incident_complaints",
        Base.metadata,
        Column("incident_id", UUIDType(), ForeignKey("incidents.id"), primary_key=True),
        Column("complaint_id", UUIDType(), ForeignKey("complaints.id"), primary_key=True),
        Column("relationship_score", Float),
        Column("relationship_reason", JSONB),
    )


complaint_orders = get_complaint_orders_table()
complaint_relations = get_complaint_relations_table()
cluster_complaints = get_cluster_complaints_table()
incident_complaints = get_incident_complaints_table()

# Add relationships to Complaint model after tables are defined
Complaint.incidents = relationship(
    "Incident",
    secondary=incident_complaints,
    back_populates="complaints",
)
Complaint.clusters = relationship(
    "ComplaintCluster",
    secondary=cluster_complaints,
    primaryjoin=Complaint.id == cluster_complaints.c.complaint_id,
    secondaryjoin=ComplaintCluster.id == cluster_complaints.c.cluster_id,
    back_populates="complaints",
)
ComplaintCluster.complaints = relationship(
    "Complaint",
    secondary=cluster_complaints,
    back_populates="clusters",
)
