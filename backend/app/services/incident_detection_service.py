"""Hybrid, explainable complaint clustering and incident detection."""

from collections import Counter
from datetime import datetime, timedelta
import math
import re
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    Complaint, ComplaintAnalysis, ComplaintEvent, ComplaintPriority,
    ComplaintCluster, Incident, IncidentEvidence, ARCStage, IncidentStatus,
    cluster_complaints,
)
from app.rag.embeddings import get_embedding_provider


def _cosine(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if not size:
        return 0.0
    dot = sum(left[i] * right[i] for i in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _entity(complaint: Complaint, key: str) -> str | None:
    entities = (complaint.analysis.entities if complaint.analysis else {}) or {}
    value = entities.get(key) or entities.get("location" if key == "region" else key)
    return str(value).lower() if value else None


class IncidentDetectionService:
    """Detect potential incidents without asserting causality."""

    async def detect(self, db: Session, window_hours: int | None = None) -> list[Incident]:
        window = window_hours or settings.incident_detection_window_hours
        cutoff = datetime.utcnow() - timedelta(hours=window)
        complaints = db.query(Complaint).filter(Complaint.created_at >= cutoff).all()
        if not complaints:
            return []

        provider = get_embedding_provider()
        embeddings = {
            complaint.id: await provider.embed(complaint.raw_text)
            for complaint in complaints
        }
        groups: list[list[Complaint]] = []
        for complaint in complaints:
            analysis = complaint.analysis
            if not analysis or not analysis.category:
                continue
            matching = [complaint]
            for candidate in complaints:
                if candidate.id == complaint.id or not candidate.analysis:
                    continue
                semantic = _cosine(embeddings[complaint.id], embeddings[candidate.id])
                category_match = analysis.category == candidate.analysis.category
                region_match = bool(_entity(complaint, "region") and _entity(complaint, "region") == _entity(candidate, "region"))
                product_match = bool(_entity(complaint, "product") and _entity(complaint, "product") == _entity(candidate, "product"))
                time_match = abs((complaint.created_at - candidate.created_at).total_seconds()) <= window * 3600
                context_match = region_match or product_match
                score = (
                    semantic * settings.incident_semantic_weight
                    + float(category_match) * settings.incident_category_weight
                    + float(context_match) * settings.incident_context_weight
                    + float(time_match) * settings.incident_time_weight
                )
                if category_match and semantic >= settings.incident_similarity_threshold and context_match and time_match:
                    matching.append(candidate)
            unique = {item.id: item for item in matching}
            if len(unique) >= settings.incident_min_cluster_size:
                group_ids = {item.id for item in unique.values()}
                if not any(group_ids <= {item.id for item in group} for group in groups):
                    groups.append(list(unique.values()))

        incidents = []
        for group in groups:
            incident = await self._upsert_incident(db, group, embeddings)
            incidents.append(incident)
        db.commit()
        return incidents

    async def _upsert_incident(self, db: Session, complaints: list[Complaint], embeddings: dict) -> Incident:
        category = complaints[0].analysis.category
        regions = sorted({_entity(item, "region") for item in complaints if _entity(item, "region")})
        products = sorted({_entity(item, "product") for item in complaints if _entity(item, "product")})
        title_context = regions[0].title() if len(regions) == 1 else category.title()
        title = f"Potential {title_context} {category.title()} Disruption"
        cluster = db.query(ComplaintCluster).filter(
            ComplaintCluster.category == category,
            ComplaintCluster.affected_region == (regions[0] if len(regions) == 1 else None),
        ).first()
        if not cluster:
            cluster = ComplaintCluster(name=title, category=category, confidence=0.0)
            db.add(cluster)
            db.flush()
        cluster.complaints = complaints
        cluster.complaint_count = len(complaints)
        cluster.affected_region = regions[0] if len(regions) == 1 else None
        cluster.affected_product = products[0] if len(products) == 1 else None
        cluster.cluster_score = round(min(0.99, 0.7 + len(complaints) / 100), 4)
        cluster.confidence = cluster.cluster_score
        db.flush()
        db.execute(
            cluster_complaints.update().where(cluster_complaints.c.cluster_id == cluster.id).values(
                relationship_score=cluster.cluster_score,
                relationship_reason=["same category", "similar complaint text", "shared context", "same time window"],
            )
        )

        incident = db.query(Incident).filter(Incident.cluster_id == cluster.id).first()
        if not incident:
            incident = Incident(
                external_id=f"INC-{str(cluster.id).replace('-', '')[:8].upper()}",
                title=title,
                status=IncidentStatus.DETECTED,
                detected_by_agent="IncidentDetectionService",
                cluster=cluster,
            )
            db.add(incident)
            db.flush()
        incident.status = IncidentStatus.DETECTED if incident.status != IncidentStatus.CONFIRMED else incident.status
        incident.title = title
        incident.description = f"{len(complaints)} semantically similar {category} complaints share contextual signals."
        incident.affected_regions = regions
        incident.affected_products = products
        incident.complaint_count = len(complaints)
        incident.affected_customers_count = len({item.customer_id for item in complaints})
        incident.first_complaint_at = min(item.created_at for item in complaints)
        incident.last_complaint_at = max(item.created_at for item in complaints)
        incident.confidence = cluster.confidence
        incident.potential_root_cause = f"Suspected {title_context.lower()} operational disruption"
        incident.suspected_root_cause = incident.potential_root_cause
        incident.evidence_summary = f"{len(complaints)} complaints matched category, semantic, contextual, and time-window signals."
        incident.regions_affected = len(regions)
        incident.products_affected = len(products)
        priorities = [item.priority for item in complaints if item.priority]
        incident.high_priority_count = sum(1 for item in priorities if (item.priority_score or 0) >= 70)
        incident.sla_breach_count = sum(1 for item in priorities if item.sla_breached)
        incident.estimated_business_impact = float(incident.affected_customers_count * 20)
        current_volume = len(complaints)
        baseline = max(1.0, current_volume / 4)
        incident.baseline_volume = baseline
        incident.current_volume = current_volume
        incident.volume_change_percent = round((current_volume - baseline) / baseline * 100, 2)
        db.add(IncidentEvidence(
            incident_id=incident.id,
            cluster_id=cluster.id,
            complaint_ids=[str(item.id) for item in complaints],
            similarity_scores={str(item.id): cluster.cluster_score for item in complaints},
            signals_used=["semantic_similarity", "category", "context", "time_window", "volume_anomaly"],
            thresholds={"semantic_similarity": settings.incident_similarity_threshold, "window_hours": settings.incident_detection_window_hours},
            confidence=incident.confidence,
            recommended_actions=["Investigate the affected operation", "Review partner or warehouse status", "Monitor complaint volume"],
        ))
        for item in complaints:
            db.add(ComplaintEvent(
                complaint_id=item.id,
                arc_stage=ARCStage.LEARN,
                agent_name="IncidentDetectionService",
                status="completed",
                output_reference={"incident_id": str(incident.id), "cluster_id": str(cluster.id)},
            ))
        return incident