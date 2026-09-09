from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Complaint, ComplaintAnalysis, Customer, Incident, KnowledgeDocument, Order, ResolutionRecommendation


class KnowledgeGraphService:
    """Simple relational knowledge graph built over existing ResolveIQ entities."""

    def build_graph(self, db: Session, center_type: str | None = None, center_id: str | None = None, limit: int = 40) -> dict[str, Any]:
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        seen_edges: set[tuple[str, str, str]] = set()

        def add_node(entity_type: str, entity_id: str, name: str, metadata: dict[str, Any] | None = None, status: str | None = None):
            key = f"{entity_type}:{entity_id}"
            if key not in nodes:
                nodes[key] = {
                    "id": entity_id,
                    "type": entity_type,
                    "label": name,
                    "status": status or "known",
                    "metadata": metadata or {},
                }
            return key

        def add_edge(source: str, target: str, relation: str, metadata: dict[str, Any] | None = None):
            if source == target:
                return
            edge_key = (source, target, relation)
            if edge_key in seen_edges:
                return
            seen_edges.add(edge_key)
            edges.append({
                "source": source,
                "target": target,
                "type": relation,
                "metadata": metadata or {},
            })

        customer_entities = db.query(Customer).limit(limit).all()
        for customer in customer_entities:
            cid = str(customer.id)
            add_node("customer", cid, customer.name, {"tier": customer.tier, "email": customer.email}, customer.account_status)
            for order in db.query(Order).filter(Order.customer_id == customer.id).limit(limit).all():
                oid = str(order.id)
                add_node("order", oid, order.product or "Order", {"status": order.status, "amount": float(order.amount or 0)}, order.status)
                add_edge(cid, oid, "placed")
                add_edge(oid, cid, "belongs_to")
                if order.product:
                    add_edge(oid, order.product.lower(), "contains", {"entity_type": "product"})
            for complaint in db.query(Complaint).filter(Complaint.customer_id == customer.id).limit(limit).all():
                complaint_id = str(complaint.id)
                complaint_label = f"Complaint {str(complaint.id)[:8]}"
                add_node("complaint", complaint_id, complaint_label, {"status": complaint.status.value if complaint.status else "received"}, complaint.status.value if complaint.status else "received")
                add_edge(cid, complaint_id, "submitted")
                add_edge(complaint_id, cid, "for_customer")
                analysis = complaint.analysis
                if analysis and analysis.entities:
                    if analysis.entities.get("product"):
                        product_name = str(analysis.entities["product"])
                        add_node("product", product_name, product_name, {}, "known")
                        add_edge(complaint_id, product_name, "concerns")
                    if analysis.entities.get("region"):
                        region_name = str(analysis.entities["region"])
                        add_node("region", region_name, region_name, {}, "known")
                        add_edge(complaint_id, region_name, "affects_region")
                rec = complaint.resolution_recommendation if hasattr(complaint, "resolution_recommendation") else None
                if rec:
                    resolution_id = str(rec.id) if hasattr(rec, "id") else f"resolution-{complaint_id}"
                    add_node("resolution", resolution_id, rec.recommended_action[:30], {"confidence": rec.confidence}, "resolved")
                    add_edge(resolution_id, complaint_id, "resolves")
                for incident in complaint.incidents:
                    incident_id = str(incident.id)
                    add_node("incident", incident_id, incident.title, {"confidence": incident.confidence}, incident.status.value if incident.status else "detected")
                    add_edge(complaint_id, incident_id, "related_to")
                    add_edge(incident_id, complaint_id, "affects_complaint")

        for complaint in db.query(Complaint).limit(limit).all():
            complaint_id = str(complaint.id)
            if complaint_id not in {node["id"] for node in nodes.values() if node["type"] == "complaint"}:
                complaint_label = f"Complaint {str(complaint.id)[:8]}"
                add_node("complaint", complaint_id, complaint_label, {"status": complaint.status.value if complaint.status else "received"}, complaint.status.value if complaint.status else "received")
            for incident in complaint.incidents:
                iid = str(incident.id)
                add_node("incident", iid, incident.title, {"confidence": incident.confidence}, incident.status.value if incident.status else "detected")
                add_edge(complaint_id, iid, "related_to")
                add_edge(iid, complaint_id, "affects_complaint")
                add_edge(complaint_id, iid, "linked_to")

        for document in db.query(KnowledgeDocument).limit(limit).all():
            did = str(document.id)
            add_node("policy", did, document.title, {"category": document.category, "type": document.document_type}, "published")
            for complaint in db.query(Complaint).filter(Complaint.raw_text.ilike(f"%{document.category or document.title}%")).limit(limit).all():
                complaint_id = str(complaint.id)
                if complaint_id in {n["id"] for n in nodes.values() if n["type"] == "complaint"}:
                    add_edge(complaint_id, did, "grounded_by")

        if center_type and center_id:
            center_key = f"{center_type}:{center_id}"
            nodes = {key: node for key, node in nodes.items() if key == center_key or key.startswith(f"{center_type}:") or key.startswith("complaint:") or key.startswith("order:") or key.startswith("incident:") or key.startswith("policy:") or key.startswith("product:") or key.startswith("region:")}
        
        graph = {
            "nodes": list(nodes.values()),
            "edges": edges,
            "center_type": center_type,
            "center_id": center_id,
        }
        return graph

    def get_entity_context(self, db: Session, entity_type: str, entity_id: str) -> dict[str, Any]:
        entity_map = {
            "customer": db.query(Customer).filter(Customer.id == entity_id).first(),
            "complaint": db.query(Complaint).filter(Complaint.id == entity_id).first(),
            "order": db.query(Order).filter(Order.id == entity_id).first(),
            "incident": db.query(Incident).filter(Incident.id == entity_id).first(),
            "policy": db.query(KnowledgeDocument).filter(KnowledgeDocument.id == entity_id).first(),
        }
        entity = entity_map.get(entity_type)
        if not entity:
            return {"entity_type": entity_type, "entity_id": entity_id, "metadata": {}}
        if entity_type == "customer":
            return {
                "entity_type": "customer",
                "entity_id": str(entity.id),
                "name": entity.name,
                "status": entity.account_status,
                "metadata": {
                    "tier": entity.tier,
                    "email": entity.email,
                    "complaints_count": entity.complaints_count,
                    "lifetime_value": entity.lifetime_value,
                },
            }
        if entity_type == "complaint":
            return {
                "entity_type": "complaint",
                "entity_id": str(entity.id),
                "name": f"Complaint {str(entity.id)[:8]}",
                "status": entity.status.value if entity.status else "received",
                "metadata": {
                    "channel": entity.channel.value if entity.channel else None,
                    "category": entity.analysis.category if entity.analysis else None,
                    "sentiment": entity.analysis.sentiment.value if entity.analysis and entity.analysis.sentiment else None,
                },
            }
        if entity_type == "incident":
            return {
                "entity_type": "incident",
                "entity_id": str(entity.id),
                "name": entity.title,
                "status": entity.status.value if entity.status else "detected",
                "metadata": {
                    "confidence": entity.confidence,
                    "affected_regions": entity.affected_regions,
                    "potential_root_cause": entity.potential_root_cause,
                },
            }
        return {"entity_type": entity_type, "entity_id": entity_id, "metadata": {}}

    def get_related_entities(self, db: Session, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        graph = self.build_graph(db, entity_type, entity_id)
        return [
            {"type": edge["type"], "source": edge["source"], "target": edge["target"], "metadata": edge["metadata"]}
            for edge in graph["edges"]
            if edge["source"] == entity_id or edge["target"] == entity_id
        ]

    def find_related_complaints(self, db: Session, customer_id: str) -> list[dict[str, Any]]:
        complaints = db.query(Complaint).filter(Complaint.customer_id == customer_id).all()
        return [{"id": str(item.id), "status": item.status.value if item.status else None, "category": item.analysis.category if item.analysis else None} for item in complaints]

    def find_related_incident(self, db: Session, complaint_id: str) -> list[dict[str, Any]]:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return []
        return [{"id": str(item.id), "title": item.title, "confidence": item.confidence} for item in complaint.incidents]

    def find_policy_connections(self, db: Session, complaint_id: str) -> list[dict[str, Any]]:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return []
        docs = db.query(KnowledgeDocument).all()
        matches = []
        for doc in docs:
            if complaint.analysis and complaint.analysis.category and doc.category == complaint.analysis.category:
                matches.append({"id": str(doc.id), "title": doc.title, "category": doc.category})
        return matches

    def traverse_relationships(self, db: Session, entity_type: str, entity_id: str, max_depth: int = 2) -> list[dict[str, Any]]:
        graph = self.build_graph(db, entity_type, entity_id)
        if max_depth <= 1:
            return graph["edges"]
        return graph["edges"]
