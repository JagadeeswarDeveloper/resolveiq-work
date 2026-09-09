"""Local semantic policy retrieval and lightweight reranking."""

import math
import re
from sqlalchemy.orm import Session

from app.models import KnowledgeChunk
from app.rag.embeddings import get_embedding_provider


def _cosine(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if not size:
        return 0.0
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


class PolicyRetriever:
    """Retrieve chunks using cosine similarity plus keyword overlap."""

    async def search(self, db: Session, query: str, limit: int = 5, policy_type: str | None = None) -> list[dict]:
        query_vector = await get_embedding_provider().embed(query)
        query_words = set(re.findall(r"[a-z0-9]+", query.lower()))
        results = []
        chunks = db.query(KnowledgeChunk).all()
        for chunk in chunks:
            # Skip chunks without an associated document (data integrity issue)
            if chunk.document is None:
                continue
            metadata = chunk.chunk_metadata or {}
            if policy_type and metadata.get("policy_type") != policy_type:
                continue
            semantic = _cosine(query_vector, chunk.embedding or [])
            content_words = set(re.findall(r"[a-z0-9]+", chunk.content.lower()))
            title_words = set(re.findall(r"[a-z0-9]+", chunk.document.title.lower()))
            overlap = len(query_words & content_words) / max(len(query_words), 1)
            title_overlap = len(query_words & title_words) / max(len(query_words), 1)
            query_text = query.lower()
            security_terms = (
                "unauthorized", "account takeover", "changed the email", "payment method",
                "can't log in", "cannot log in", "do not recognize", "don't recognize",
            )
            security_query = sum(term in query_text for term in security_terms)
            security_policy = any(term in (chunk.document.title + " " + chunk.content).lower() for term in (
                "account security", "unauthorized access", "account takeover", "security reviewer",
            ))
            domain_boost = 0.45 if security_query and security_policy else 0.0
            score = min(1.0, semantic * 0.45 + overlap * 0.25 + title_overlap * 0.30 + domain_boost)
            results.append({
                "document_id": str(chunk.document_id),
                "document": chunk.document.title,
                "chunk_id": str(chunk.id),
                "content": chunk.content,
                "score": round(score, 4),
                "metadata": metadata,
            })
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
