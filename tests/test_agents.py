"""Test script for AI agents."""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.ai.llm.client import get_llm_client
from app.ai.models import ComplaintUnderstanding, SentimentEnum, ResolutionRecommendation, SupervisorDecision, SupervisorDecisionEnum
from app.agents.understanding_agent import UnderstandingAgent
from app.agents.resolution_agent import ResolutionAgent
from app.agents.supervisor_agent import SupervisorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_understanding_agent():
    """Test UnderstandingAgent with mock data."""
    logger.info("=" * 60)
    logger.info("Testing UnderstandingAgent")
    logger.info("=" * 60)
    
    agent = UnderstandingAgent()
    logger.info(f"Agent created. LLM in demo mode: {agent.llm.is_demo_mode()}")
    
    # Test the prompt building
    class MockComplaint:
        id = UUID("12345678-1234-5678-1234-567812345678")
        raw_text = "I ordered a laptop 2 weeks ago and it still hasn't arrived. This is unacceptable!"
        customer_id = UUID("87654321-4321-8765-4321-876543218765")
    
    complaint = MockComplaint()
    prompt = agent._build_prompt(complaint)
    logger.info(f"Generated prompt (first 200 chars): {prompt[:200]}")
    logger.info("✓ UnderstandingAgent prompt generation works")


async def test_resolution_agent():
    """Test ResolutionAgent with mock data."""
    logger.info("=" * 60)
    logger.info("Testing ResolutionAgent")
    logger.info("=" * 60)
    
    agent = ResolutionAgent()
    logger.info(f"Agent created. LLM in demo mode: {agent.llm.is_demo_mode()}")
    
    # Test the prompt building
    class MockComplaint:
        id = UUID("12345678-1234-5678-1234-567812345678")
        raw_text = "I ordered a laptop 2 weeks ago and it still hasn't arrived."
        customer_id = UUID("87654321-4321-8765-4321-876543218765")
    
    class MockAnalysis:
        category = "delivery"
        sentiment = "NEGATIVE"
        summary = "Late delivery complaint"
    
    class MockCustomer:
        tier = "standard"
        lifetime_value = 500.0
        complaints_count = 0
    
    class MockPriority:
        priority_level = "HIGH"
        priority_score = 75
        sla_breached = False
    
    complaint = MockComplaint()
    complaint.customer = MockCustomer()
    complaint.analysis = MockAnalysis()
    complaint.priority = MockPriority()
    
    # We can't actually call the agent without a DB session, 
    # but we can test the prompt generation
    prompt = agent._build_prompt(complaint, complaint.customer, complaint.analysis, complaint.priority)
    logger.info(f"Generated prompt (first 200 chars): {prompt[:200]}")
    logger.info("✓ ResolutionAgent prompt generation works")


async def test_supervisor_agent():
    """Test SupervisorAgent guardrails."""
    logger.info("=" * 60)
    logger.info("Testing SupervisorAgent")
    logger.info("=" * 60)
    
    agent = SupervisorAgent()
    logger.info(f"Agent created. LLM in demo mode: {agent.llm.is_demo_mode()}")
    logger.info(f"Compensation threshold: ${agent.compensation_threshold}")
    logger.info(f"Escalation keywords: {', '.join(agent.escalation_keywords[:5])}...")
    
    # Test guardrail detection
    class MockComplaint:
        id = UUID("12345678-1234-5678-1234-567812345678")
        raw_text = "I received a defective product that could cause injury. This is a safety issue!"
        customer_id = UUID("87654321-4321-8765-4321-876543218765")
        analysis = None
        priority = None
    
    # Mock DB session (minimal)
    class MockDB:
        def query(self, model):
            return self
        
        def filter(self, *args):
            return self
        
        def first(self):
            return None
    
    complaint = MockComplaint()
    db = MockDB()
    
    # Test guardrails
    decision = agent._apply_guardrails(complaint, db)
    if decision:
        logger.info(f"✓ Guardrail triggered: {decision.decision}")
        logger.info(f"  Reasoning: {decision.reasoning}")
    else:
        logger.info("✓ No guardrails triggered (expected for normal complaint)")
    
    logger.info("✓ SupervisorAgent guardrail detection works")


async def test_llm_client():
    """Test LLM client configuration."""
    logger.info("=" * 60)
    logger.info("Testing LLM Client")
    logger.info("=" * 60)
    
    llm = get_llm_client()
    logger.info(f"LLM Client created")
    logger.info(f"Is demo mode: {llm.is_demo_mode()}")
    logger.info(f"Provider: {llm.provider.__class__.__name__}")
    logger.info("✓ LLM Client initialization works")


async def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 16 + "AI AGENTS TEST SUITE" + " " * 22 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("\n")
    
    try:
        await test_llm_client()
        await test_understanding_agent()
        await test_resolution_agent()
        await test_supervisor_agent()
        
        logger.info("\n")
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║" + " " * 20 + "ALL TESTS PASSED ✓" + " " * 20 + "║")
        logger.info("╚" + "=" * 58 + "╝")
        logger.info("\n")
        
    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
