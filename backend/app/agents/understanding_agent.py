"""Understanding Agent - analyzes and classifies complaints."""

import logging
import time
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import Complaint, ComplaintAnalysis, AgentExecution, ARCStage, Sentiment, Severity
from app.ai.llm.client import get_llm_client
from app.ai.models import ComplaintUnderstanding, SentimentEnum
from app.ai.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class UnderstandingAgent:
    """AI agent for complaint understanding and analysis."""

    def __init__(self):
        self.llm = get_llm_client()
        self.agent_name = "UnderstandingAgent"

    async def analyze(
        self, 
        db: Session, 
        complaint: Complaint,
    ) -> ComplaintAnalysis:
        """Analyze complaint and extract understanding."""
        
        execution_start = time.time()
        execution = AgentExecution(
            complaint_id=complaint.id,
            agent_name=self.agent_name,
            arc_stage=ARCStage.UNDERSTAND,
            status="in_progress",
            started_at=datetime.utcnow(),
            is_demo_mode=self.llm.is_demo_mode(),
        )
        
        try:
            # Build prompt
            prompt = self._build_prompt(complaint)
            
            # Call LLM with structured output
            logger.info(f"Understanding Agent analyzing complaint {complaint.id}")
            response = await self.llm.generate_structured(
                prompt=prompt,
                schema=ComplaintUnderstanding,
                temperature=0.7,
            )
            
            # Parse response
            data = response.data
            understanding = ComplaintUnderstanding(**data)
            
            # Map sentiment to database enum
            sentiment_map = {
                SentimentEnum.POSITIVE: Sentiment.POSITIVE,
                SentimentEnum.NEUTRAL: Sentiment.NEUTRAL,
                SentimentEnum.FRUSTRATED: Sentiment.NEGATIVE,
                SentimentEnum.ANGRY: Sentiment.HIGHLY_NEGATIVE,
                SentimentEnum.CRITICAL: Sentiment.HIGHLY_NEGATIVE,
            }
            
            # Map urgency to severity for now (can be refined)
            severity_map = {
                "LOW": Severity.LOW,
                "MEDIUM": Severity.MEDIUM,
                "HIGH": Severity.HIGH,
                "CRITICAL": Severity.CRITICAL,
            }
            
            # Create or update analysis
            analysis = db.query(ComplaintAnalysis).filter(
                ComplaintAnalysis.complaint_id == complaint.id
            ).first()
            
            if not analysis:
                analysis = ComplaintAnalysis(complaint_id=complaint.id)
            
            analysis.category = understanding.category
            analysis.subcategory = understanding.subcategory
            analysis.intent = understanding.intent
            analysis.sentiment = sentiment_map.get(understanding.sentiment, Sentiment.NEUTRAL)
            analysis.sentiment_score = understanding.sentiment_score
            analysis.severity = severity_map.get(understanding.urgency, Severity.MEDIUM)
            analysis.summary = understanding.summary
            analysis.entities = understanding.entities.model_dump(exclude_none=True)
            analysis.key_issues = [understanding.intent]
            
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
            # Record successful execution
            latency_ms = int((time.time() - execution_start) * 1000)
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = latency_ms
            execution.model_used = response.model
            execution.tokens_used = response.tokens_used
            execution.output_summary = {
                "category": analysis.category,
                "sentiment": analysis.sentiment,
                "urgency": understanding.urgency,
            }
            
            logger.info(f"Understanding Agent completed in {latency_ms}ms")
            
        except Exception as e:
            logger.error(f"Understanding Agent error: {e}")
            latency_ms = int((time.time() - execution_start) * 1000)
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = latency_ms
            execution.error_message = str(e)
            raise
        
        finally:
            db.add(execution)
            db.commit()
        
        return analysis

    def _build_prompt(self, complaint: Complaint) -> str:
        """Build prompt for complaint analysis."""
        return PromptTemplates.UNDERSTANDING.analyze_complaint(complaint.raw_text)

    def _map_sentiment(self, sentiment_enum: SentimentEnum) -> Sentiment:
        """Map AI sentiment to database sentiment."""
        mapping = {
            SentimentEnum.POSITIVE: Sentiment.POSITIVE,
            SentimentEnum.NEUTRAL: Sentiment.NEUTRAL,
            SentimentEnum.FRUSTRATED: Sentiment.NEGATIVE,
            SentimentEnum.ANGRY: Sentiment.HIGHLY_NEGATIVE,
            SentimentEnum.CRITICAL: Sentiment.HIGHLY_NEGATIVE,
        }
        return mapping.get(sentiment_enum, Sentiment.NEUTRAL)
