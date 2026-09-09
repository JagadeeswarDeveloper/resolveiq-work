from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter()
service = KnowledgeGraphService()


@router.get("/entity")
async def graph_entity(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    return service.get_entity_context(db, entity_type, entity_id)


@router.get("/neighbors")
async def graph_neighbors(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    return {"entity_type": entity_type, "entity_id": entity_id, "neighbors": service.get_related_entities(db, entity_type, entity_id)}


@router.get("/")
async def graph_overview(
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    limit: int = Query(40, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return service.build_graph(db, center_type=entity_type, center_id=entity_id, limit=limit)


@router.get("/{entity_type}/{entity_id}")
async def graph_entity_detail(
    entity_type: str,
    entity_id: UUID,
    db: Session = Depends(get_db),
):
    return service.get_entity_context(db, entity_type, str(entity_id))
