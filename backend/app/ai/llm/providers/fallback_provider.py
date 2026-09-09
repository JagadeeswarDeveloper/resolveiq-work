"""Fallback/mock LLM provider for demo mode."""

import json
import logging
from typing import Optional
from pydantic import BaseModel

from app.ai.llm.base import LLMProvider, LLMResponse, StructuredLLMResponse, EmbeddingResponse

logger = logging.getLogger(__name__)


class FallbackProvider(LLMProvider):
    """Fallback provider for demo/testing without real LLM."""

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text from prompt."""
        logger.info("Using fallback LLM provider (demo mode)")
        return LLMResponse(
            content="[Demo Mode] This is a fallback response. Configure a real LLM provider for production.",
            tokens_used=10,
            model="fallback",
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: BaseModel,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> StructuredLLMResponse:
        """Generate structured output matching schema using deterministic logic."""
        logger.info("Using fallback LLM provider (demo mode) - deterministic output")
        
        # Generate deterministic fallback data based on schema
        data = self._generate_deterministic_output(schema, prompt)
        
        return StructuredLLMResponse(
            data=data,
            tokens_used=50,
            model="fallback",
        )

    def _generate_deterministic_output(self, schema: BaseModel, prompt: str) -> dict:
        """Generate deterministic output based on the schema and prompt."""
        prompt_lower = prompt.lower()
        complaint_text = prompt_lower
        if "complaint summary:" in prompt_lower:
            complaint_text = prompt_lower.split("complaint summary:", 1)[1].split("resolution recommendation:", 1)[0]
        elif "complaint:" in prompt_lower:
            complaint_text = prompt_lower.split("complaint:", 1)[1]
            for section in ("analysis:", "analysis requirements:", "customer context:", "policy evidence"):
                complaint_text = complaint_text.split(section, 1)[0]
        is_faq = any(term in complaint_text for term in ("how do i", "where can i", "what is", "password", "reset"))
        is_account_takeover = any(term in complaint_text for term in (
            "changed the email", "email address", "can't log in", "cannot log in",
            "no longer log in", "account takeover", "taken over", "unauthorized",
            "don't recognize", "do not recognize", "payment method",
        ))
        is_risk = is_account_takeover or any(term in complaint_text for term in ("fraud", "legal", "safety", "regulatory", "criminal", "injury"))
        is_delivery = any(term in complaint_text for term in ("delivery", "delivered", "package", "shipment", "arrive", "order"))
        is_billing = any(term in complaint_text for term in ("charged", "charge", "invoice", "billing", "payment"))
        # Extract field names from schema
        fields = schema.model_fields
        output = {}
        
        # Generate sensible defaults based on field names
        for field_name, field_info in fields.items():
            field = field_name.lower()
            if field in {"guardrails_applied", "risk_factors", "policy_sources", "incident_signals", "other_entities"}:
                output[field_name] = []
            elif field == "internal_actions":
                output[field_name] = (
                    [
                        "Lock suspicious account activity",
                        "Verify identity through a trusted channel",
                        "Review login, email, and payment-method changes",
                        "Escalate to a human security reviewer",
                    ] if is_account_takeover else []
                )
            elif field == "compensation":
                output[field_name] = (
                    None if is_account_takeover or is_faq else
                    {"type": "credit", "amount": 20, "reason": "Delivery delay service credit"}
                )
            elif field == "entities":
                output[field_name] = {
                    "order_id": None,
                    "product": None,
                    "location": None,
                    "account_issue": "suspected account takeover" if is_account_takeover else None,
                    "payment": "unrecognized payment method" if is_account_takeover else None,
                    "other_entities": ["unauthorized email change"] if is_account_takeover else [],
                }
            elif field == "sentiment_score" or field.endswith("_score"):
                output[field_name] = 0.65
            elif field == "category":
                output[field_name] = "account" if is_account_takeover or is_faq else "billing" if is_billing and not is_delivery else "delivery" if is_delivery else "customer_service"
            elif field == "sentiment":
                output[field_name] = "CRITICAL" if is_account_takeover else "NEUTRAL" if is_faq else "FRUSTRATED"
            elif "summary" in field:
                output[field_name] = (
                    "Customer reports an unauthorized email change, loss of account access, and an unrecognized payment method; immediate security review is required."
                    if is_account_takeover else "Customer asks for password reset instructions." if is_faq
                    else "Customer reports delay and frustration with support response."
                )
            elif field == "urgency":
                output[field_name] = "CRITICAL" if is_account_takeover else "LOW" if is_faq else "HIGH"
            elif field == "product":
                output[field_name] = "Electronic device"
            elif field == "intent":
                output[field_name] = "Secure account and investigate unauthorized changes" if is_account_takeover else "Reset account password" if is_faq else "Request resolution for delivery issue"
            elif field == "subcategory":
                output[field_name] = "Suspected account takeover" if is_account_takeover else "Password reset" if is_faq else "Late delivery"
            elif field in {"reason", "reasoning", "reasoning_summary"}:
                output[field_name] = "Complaint shows frustration and potential repeat issue."
            elif field == "recommended_action":
                output[field_name] = (
                    "Escalate to the security team, lock suspicious account activity, verify identity through a trusted channel, reverse unauthorized payment changes, and restore access only after verification."
                    if is_account_takeover else "Provide password reset instructions" if is_faq else "Process refund and provide service credit"
                )
            elif field == "customer_response":
                output[field_name] = (
                    "We are treating this as a potential account takeover. We have escalated it to our security team. Please do not share passwords or payment details; we will verify your identity through a trusted channel before making account changes."
                    if is_account_takeover else "Use the password reset link to securely choose a new password." if is_faq else "We apologize for the delay. We are processing a resolution."
                )
            elif field == "confidence":
                output[field_name] = 0.8
            elif field == "decision":
                if is_account_takeover:
                    output[field_name] = "ESCALATE"
                elif is_faq and not is_risk:
                    output[field_name] = "AUTO_RESOLVE"
                elif is_risk:
                    output[field_name] = "ESCALATE"
                else:
                    output[field_name] = "HUMAN_APPROVAL"
            elif field == "requires_human_review":
                output[field_name] = not is_faq or is_risk
            else:
                # Use field type to set a sensible default
                if field_info.annotation in (str, type(Optional[str])):
                    output[field_name] = ""
                elif field_info.annotation in (int, type(Optional[int])):
                    output[field_name] = 0
                elif field_info.annotation in (float, type(Optional[float])):
                    output[field_name] = 0.0
                elif field_info.annotation in (bool, type(Optional[bool])):
                    output[field_name] = False
                elif field_info.annotation in (list, type(Optional[list])):
                    output[field_name] = []
                elif field_info.annotation in (dict, type(Optional[dict])):
                    output[field_name] = {}
                else:
                    output[field_name] = None
        
        return output

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embedding for text."""
        logger.info("Using fallback embedding (demo mode)")
        # Return a fixed-size vector for testing
        return EmbeddingResponse(
            embedding=[0.0] * 1536,  # Default embedding size
            model="fallback",
        )

    def is_available(self) -> bool:
        """Fallback is always available."""
        return True
