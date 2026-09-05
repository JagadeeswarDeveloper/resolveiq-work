"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from app.models import (
    ARCStage as ARCStageSchema,
    Channel as ChannelSchema,
    ComplaintStatus as ComplaintStatusSchema,
    PriorityLevel as PriorityLevelSchema,
    Sentiment as SentimentSchema,
)


# ============================================================================
# Enums
# ============================================================================


# ============================================================================
# Customer Schemas
# ============================================================================


class CustomerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    tier: str = "standard"
    account_status: str = "active"


class CustomerCreate(CustomerBase):
    external_id: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: UUID
    external_id: Optional[str]
    lifetime_value: float
    complaints_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Complaint Schemas
# ============================================================================


class ComplaintCreate(BaseModel):
    customer_id: Optional[UUID] = None
    customer_email: Optional[str] = None
    channel: ChannelSchema
    raw_text: str
    language: str = "en"
    metadata: Optional[dict] = None


class ComplaintAnalysisSchema(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    sentiment: Optional[SentimentSchema] = None
    sentiment_score: Optional[float] = None
    severity: Optional[str] = None
    entities: Optional[dict] = None
    summary: Optional[str] = None
    key_issues: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ComplaintPrioritySchema(BaseModel):
    priority_score: Optional[int] = None
    priority_level: Optional[PriorityLevelSchema] = None
    sla_breached: bool = False
    reasons: Optional[List[str]] = None

    class Config:
        from_attributes = True


class PolicyEvidenceSchema(BaseModel):
    document: str
    content: str
    score: float
    metadata: Optional[dict] = None


class ResolutionRecommendationSchema(BaseModel):
    recommended_action: str
    customer_response: Optional[str] = None
    compensation: Optional[dict] = None
    reasoning_summary: Optional[str] = None
    confidence: Optional[float] = None
    requires_human_review: bool = False
    policy_sources: Optional[List[str]] = None
    policy_evidence: List[PolicyEvidenceSchema] = []
    policy_confidence: float = 0.0

    class Config:
        from_attributes = True


class ARCEventSchema(BaseModel):
    arc_stage: ARCStageSchema
    agent_name: Optional[str] = None
    status: str = "pending"
    timestamp: datetime

    class Config:
        from_attributes = True


class ComplaintResponse(BaseModel):
    id: UUID
    external_id: Optional[str]
    customer_id: UUID
    channel: ChannelSchema
    raw_text: str
    status: ComplaintStatusSchema
    analysis: Optional[ComplaintAnalysisSchema] = None
    priority: Optional[ComplaintPrioritySchema] = None
    resolution_recommendation: Optional[ResolutionRecommendationSchema] = None
    arc_events: List[ARCEventSchema] = []
    incidents: List[dict] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintListItem(BaseModel):
    id: UUID
    external_id: Optional[str]
    customer_id: UUID
    channel: ChannelSchema
    status: ComplaintStatusSchema
    raw_text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Dashboard Schemas
# ============================================================================


class DashboardSummary(BaseModel):
    total_complaints: int
    open_complaints: int
    high_priority_complaints: int
    avg_resolution_time_hours: float
    sla_breach_rate: float
    auto_resolution_rate: float
    human_approval_rate: float = 0.0
    sla_breaches: int = 0
    active_incidents: int


class ComplaintTrendData(BaseModel):
    date: str
    count: int


class CategoryDistribution(BaseModel):
    category: str
    count: int


# ============================================================================
# Incident Schemas
# ============================================================================


class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    affected_products: Optional[List[str]] = None
    affected_regions: Optional[List[str]] = None
    suspected_root_cause: Optional[str] = None


class IncidentEvidenceResponse(BaseModel):
    id: UUID
    incident_id: UUID
    cluster_id: Optional[UUID] = None
    detection_timestamp: datetime
    complaint_ids: Optional[List[str]] = None
    similarity_scores: Optional[dict] = None
    signals_used: Optional[List[str]] = None
    thresholds: Optional[dict] = None
    ai_assessment: Optional[dict] = None
    confidence: Optional[float] = None
    recommended_actions: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ComplaintClusterResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    cluster_score: float
    complaint_count: int
    affected_region: Optional[str] = None
    affected_product: Optional[str] = None
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentResponse(IncidentBase):
    id: UUID
    status: str
    complaint_count: int
    confidence: float
    evidence: Optional[dict] = None
    detected_at: datetime
    created_at: datetime
    potential_root_cause: Optional[str] = None
    evidence_summary: Optional[str] = None
    severity: Optional[str] = None
    affected_customers_count: int = 0
    high_priority_count: int = 0
    sla_breach_count: int = 0
    estimated_business_impact: float = 0.0
    regions_affected: int = 0
    products_affected: int = 0
    baseline_volume: float = 0.0
    current_volume: int = 0
    volume_change_percent: float = 0.0

    class Config:
        from_attributes = True


class KnowledgeDocumentCreate(BaseModel):
    title: str
    content: str
    document_type: str = "policy"
    category: Optional[str] = None
    version: int = 1
    source: str = "Internal knowledge"


class KnowledgeChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    content: str
    chunk_metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    document_type: Optional[str] = None
    category: Optional[str] = None
    version: int
    status: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    chunks: List[KnowledgeChunkResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# API Response Wrappers
# ============================================================================


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
