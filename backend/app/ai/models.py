"""AI models - structured output schemas for AI operations."""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class SentimentEnum(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    FRUSTRATED = "FRUSTRATED"
    ANGRY = "ANGRY"
    CRITICAL = "CRITICAL"


class UrgencyEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SupervisorDecisionEnum(str, Enum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    ESCALATE = "ESCALATE"


# ============================================================================
# COMPLAINT UNDERSTANDING
# ============================================================================


class EntityExtraction(BaseModel):
    """Extracted entities from complaint."""
    product: Optional[str] = Field(None, description="Product mentioned")
    order_id: Optional[str] = Field(None, description="Order ID if mentioned")
    location: Optional[str] = Field(None, description="Geographic location")
    account_issue: Optional[str] = Field(None, description="Account-related issues")
    payment: Optional[str] = Field(None, description="Payment-related information")
    other_entities: Optional[List[str]] = Field(default_factory=list, description="Other key entities")


class ComplaintUnderstanding(BaseModel):
    """AI-generated understanding of complaint."""
    category: str = Field(..., description="Primary complaint category")
    subcategory: Optional[str] = Field(None, description="Secondary classification")
    intent: str = Field(..., description="What customer wants/needs")
    sentiment: SentimentEnum = Field(..., description="Emotional tone")
    sentiment_score: float = Field(..., ge=0.0, le=1.0, description="Sentiment confidence 0-1")
    urgency: UrgencyEnum = Field(..., description="Operational urgency")
    summary: str = Field(..., description="Concise operational summary")
    entities: EntityExtraction = Field(..., description="Extracted entities")


# ============================================================================
# INVESTIGATION SUMMARY
# ============================================================================


class InvestigationSummary(BaseModel):
    """Summary of investigation findings."""
    related_complaints_count: int = Field(0, description="Number of related complaints found")
    repeat_customer: bool = Field(False, description="Is this customer a repeat complainer")
    potential_incident: bool = Field(False, description="Potential broader incident")
    incident_signals: List[str] = Field(default_factory=list, description="Evidence of incident")
    priority_multiplier: float = Field(1.0, ge=0.5, le=2.0, description="Factor to apply to priority")


# ============================================================================
# RESOLUTION
# ============================================================================


class CompensationRecommendation(BaseModel):
    """Compensation recommendation."""
    type: str = Field(..., description="refund, credit, replacement, etc")
    amount: Optional[float] = Field(None, description="Amount in currency")
    reason: str = Field(..., description="Justification for compensation")


class ResolutionRecommendation(BaseModel):
    """AI-generated resolution recommendation."""
    recommended_action: str = Field(..., description="What should be done")
    customer_response: str = Field(..., description="What to tell the customer")
    internal_actions: List[str] = Field(default_factory=list, description="Internal steps needed")
    compensation: Optional[CompensationRecommendation] = Field(None, description="Compensation if needed")
    reasoning_summary: str = Field(..., description="Why this recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    requires_human_review: bool = Field(False, description="Should this go to human")
    policy_sources: Optional[List[str]] = Field(default_factory=list, description="Policy citations")
    policy_evidence: List[dict] = Field(default_factory=list, description="Concise supporting policy evidence")
    policy_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in retrieved policy evidence")


# ============================================================================
# SUPERVISOR DECISION
# ============================================================================


class SupervisorDecision(BaseModel):
    """Supervisor agent decision on complaint routing."""
    decision: SupervisorDecisionEnum = Field(..., description="Routing decision")
    reasoning: str = Field(..., description="Reasoning for decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in decision")
    guardrails_applied: List[str] = Field(default_factory=list, description="Which guardrails triggered")
    escalation_reason: Optional[str] = Field(None, description="If escalating, why")
    risk_factors: List[str] = Field(default_factory=list, description="Risk indicators found")
