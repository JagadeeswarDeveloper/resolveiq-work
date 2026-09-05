"""System endpoints - health checks and status."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.ai.llm.client import get_llm_client
from app.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "ResolveIQ",
    }


@router.get("/llm-status", response_model=Dict[str, Any])
async def llm_status():
    """Get LLM provider status."""
    try:
        llm = get_llm_client()
        status = await llm.health_check()
        
        # Add additional context
        status["ai_mode"] = "live" if not llm.is_demo_mode() else "demo"
        
        return status
    except Exception as e:
        logger.error(f"Error checking LLM status: {e}")
        return {
            "provider": "unknown",
            "reachable": False,
            "error": str(e),
        }


@router.get("/system-info", response_model=APIResponse)
async def system_info(db: Session = Depends(get_db)):
    """Get system information and status."""
    try:
        llm = get_llm_client()
        
        # Get LLM status
        llm_status = await llm.health_check()
        
        # Count some useful stats
        from app.models import Complaint, AgentExecution
        
        total_complaints = db.query(Complaint).count()
        agent_executions = db.query(AgentExecution).count()
        
        return APIResponse(
            success=True,
            message="System info retrieved",
            data={
                "llm": {
                    "provider": llm_status.get("provider"),
                    "model": llm_status.get("model"),
                    "reachable": llm_status.get("reachable"),
                    "latency_ms": llm_status.get("latency_ms"),
                    "mode": "demo" if llm.is_demo_mode() else "live",
                },
                "database": {
                    "total_complaints": total_complaints,
                    "agent_executions": agent_executions,
                },
                "environment": {
                    "debug": True,  # From settings if needed
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return APIResponse(
            success=False,
            message=f"Error: {str(e)}",
            data={}
        )
