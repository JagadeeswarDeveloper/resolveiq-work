"""Serializable state carried by the complaint workflow."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComplaintWorkflowState(BaseModel):
    complaint_id: str
    workflow_id: str
    complaint: Dict[str, Any] = Field(default_factory=dict)
    customer_context: Dict[str, Any] = Field(default_factory=dict)
    understanding: Dict[str, Any] = Field(default_factory=dict)
    priority: Dict[str, Any] = Field(default_factory=dict)
    investigation: Dict[str, Any] = Field(default_factory=dict)
    related_complaints: List[str] = Field(default_factory=list)
    incident: Optional[Dict[str, Any]] = None
    policy_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    policy_evidence_available: bool = False
    resolution: Dict[str, Any] = Field(default_factory=dict)
    supervisor_decision: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    current_stage: str = "CAPTURE"
    workflow_status: str = "running"
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)