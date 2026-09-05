"""Knowledge document ingestion pipeline."""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models import KnowledgeDocument, KnowledgeChunk
from app.rag.chunking import chunk_document
from app.rag.embeddings import get_embedding_provider


async def ingest_document(db: Session, document: KnowledgeDocument) -> KnowledgeDocument:
    """Clean, chunk, embed, and replace a document's indexed chunks."""
    document.chunks.clear()
    provider = get_embedding_provider()
    for index, item in enumerate(chunk_document(document.content)):
        chunk = KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=item["content"],
            embedding=await provider.embed(item["content"]),
            chunk_metadata={
                "section": item["section"],
                "policy_type": document.document_type,
                "version": document.version,
                "effective_date": document.updated_at.isoformat() if document.updated_at else None,
                "tags": [document.category] if document.category else [],
            },
        )
        db.add(chunk)
    document.status = "ingested"
    document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(document)
    return document
