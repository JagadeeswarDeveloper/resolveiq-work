"""Prompt templates for AI agents."""

from typing import Optional, Dict, Any


class UnderstandingPrompt:
    """Prompts for UnderstandingAgent."""

    @staticmethod
    def analyze_complaint(complaint_text: str) -> str:
        """Prompt for complaint analysis."""
        return f"""You are a customer complaint analyst. Analyze this complaint with structured reasoning.

COMPLAINT:
{complaint_text}

ANALYSIS REQUIREMENTS:
1. Category: Primary issue type
   Options: delivery, billing, product_quality, account, technical, refund, customer_service, other
2. Subcategory: More specific type
3. Intent: What the customer actually wants
4. Sentiment: POSITIVE, NEUTRAL, FRUSTRATED, ANGRY, CRITICAL
5. Sentiment Score: 0.0 (positive) to 1.0 (very negative)
6. Urgency: LOW, MEDIUM, HIGH, CRITICAL
7. Summary: Concise operational summary (NOT customer-facing)
8. Entities: Extract specific details
   - product: Product/service mentioned
   - order_id: Order identifier if mentioned
   - location: Geographic location
   - account_issue: Account-related problems
   - payment: Payment-related issues

CRITICAL RULES:
- Do NOT invent information not in the complaint
- If you cannot identify a field, set it to null/empty
- Be precise and specific
- Do not be emotional
- Focus on what was reported, not interpretation

Return ONLY valid JSON, no markdown, no explanation:
{{
    "category": "string",
    "subcategory": "string or null",
    "intent": "string",
    "sentiment": "POSITIVE|NEUTRAL|FRUSTRATED|ANGRY|CRITICAL",
    "sentiment_score": 0.0-1.0,
    "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
    "summary": "string",
    "entities": {{
        "product": "string or null",
        "order_id": "string or null",
        "location": "string or null",
        "account_issue": "string or null",
        "payment": "string or null",
        "other_entities": "additional entities as string or null"
    }}
}}"""


class ResolutionPrompt:
    """Prompts for ResolutionAgent."""

    @staticmethod
    def generate_resolution(
        complaint_text: str,
        category: str,
        sentiment: str,
        customer_tier: str,
        lifetime_value: float,
        previous_complaints: int,
        policy_evidence: str = "No policy evidence was retrieved.",
    ) -> str:
        """Prompt for resolution generation."""
        return f"""You are a customer service resolution specialist. Generate a resolution based on available context.

COMPLAINT:
{complaint_text}

ANALYSIS:
- Category: {category}
- Sentiment: {sentiment}

CUSTOMER CONTEXT:
- Tier: {customer_tier}
- Lifetime Value: ${lifetime_value}
- Previous Complaints: {previous_complaints}

POLICY EVIDENCE (authoritative fictional enterprise policy excerpts):
{policy_evidence}

RESOLUTION REQUIREMENTS:
1. Recommended Action: Specific resolution (refund, replacement, credit, etc.)
2. Customer Response: Professional, empathetic customer-facing message
3. Internal Actions: Any internal steps needed
4. Compensation: If needed: {{"type": "...", "amount": ..., "reason": "..."}}
5. Reasoning Summary: Why this resolution is appropriate
6. Confidence: 0.0-1.0 confidence in recommendation
7. Requires Human Review: true if needs approval

GROUNDING RULES:
- Use only the supplied policy evidence for company policy claims.
- Do not invent company rules. If evidence is insufficient, say so.
- Distinguish policy requirements from your recommendation.
- Include concise supporting excerpts in policy_evidence.

GUIDELINES:
- Consider customer tier and history in compensation decisions
- Be empathetic but professional
- Only recommend actions within typical company policy
- Flag for human review if unclear or compensation exceeds $100
- Provide clear reasoning grounded in the complaint

Return ONLY valid JSON, no markdown:
{{
    "recommended_action": "string",
    "customer_response": "string",
    "internal_actions": ["string"],
    "compensation": {{"type": "string", "amount": number, "reason": "string"}} or null,
    "reasoning_summary": "string",
    "confidence": 0.0-1.0,
    "requires_human_review": boolean,
    "policy_sources": ["string"] or null,
    "policy_evidence": [{{"document": "string", "section": "string", "content": "string", "score": 0.0}}],
    "policy_confidence": 0.0-1.0
}}"""


class SupervisorPrompt:
    """Prompts for SupervisorAgent."""

    @staticmethod
    def decide_routing(
        complaint_text: str,
        category: str,
        sentiment: str,
        recommendation: Optional[Dict[str, Any]] = None,
        policy_evidence_available: bool = False,
    ) -> str:
        """Prompt for routing decision."""
        recommendation_str = ""
        if recommendation:
            action = recommendation.get("recommended_action", "N/A")
            compensation = recommendation.get("compensation", {})
            comp_amount = compensation.get("amount", 0) if compensation else 0
            confidence = recommendation.get("confidence", 0)
            
            recommendation_str = f"""
RESOLUTION RECOMMENDATION:
- Action: {action}
- Compensation: ${comp_amount} ({compensation.get('type', 'N/A') if compensation else 'none'})
- Confidence: {confidence}
- Requires Review: {recommendation.get('requires_human_review', False)}
"""

        return f"""You are a complaint routing supervisor. Decide how to route this complaint.

COMPLAINT SUMMARY:
- Category: {category}
- Sentiment: {sentiment}
- Text: {complaint_text[:300]}...
{recommendation_str}

ROUTING OPTIONS:
1. AUTO_RESOLVE: Low-risk, high-confidence, customer likely satisfied
2. HUMAN_APPROVAL: Requires supervisor review (moderate risk, compensation, or unclear)
3. ESCALATE: Management attention needed (legal, safety, regulatory, high-risk)

DECISION FACTORS:
- Confidence level of recommendation
- Risk to customer satisfaction
- Compensation amount
- Regulatory/legal concerns
- Customer tier and value
- Potential for incident/pattern
- Policy evidence available: {policy_evidence_available}

Return ONLY valid JSON:
{{
    "decision": "AUTO_RESOLVE|HUMAN_APPROVAL|ESCALATE",
    "reasoning": "Clear explanation of routing decision",
    "confidence": 0.0-1.0,
    "risk_factors": ["list", "of", "factors"],
    "escalation_reason": "string or null if not escalating"
}}"""


class PromptTemplates:
    """Centralized prompt management."""

    UNDERSTANDING = UnderstandingPrompt()
    RESOLUTION = ResolutionPrompt()
    SUPERVISOR = SupervisorPrompt()
