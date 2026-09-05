"""Internal knowledge management and policy retrieval endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import KnowledgeDocument
from app.rag.ingestion import ingest_document
from app.rag.service import retrieve_policy_evidence
from app.schemas import KnowledgeDocumentCreate, KnowledgeDocumentResponse

router = APIRouter()


@router.post("/documents", response_model=KnowledgeDocumentResponse)
async def create_document(payload: KnowledgeDocumentCreate, db: Session = Depends(get_db)):
    document = KnowledgeDocument(**payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return db.query(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc()).all()


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return document


@router.delete("/documents/{document_id}")
def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    title = document.title
    db.delete(document)
    db.commit()
    return {"success": True, "message": f"Knowledge document '{title}' deleted", "id": str(document_id)}


@router.post("/documents/{document_id}/ingest", response_model=KnowledgeDocumentResponse)
async def ingest(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return await ingest_document(db, document)


@router.get("/search")
async def search(q: str = Query(..., min_length=2), limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    return {"query": q, "results": await retrieve_policy_evidence(db, q, limit=limit)}
