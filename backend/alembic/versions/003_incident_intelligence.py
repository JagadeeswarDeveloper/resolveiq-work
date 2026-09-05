"""Add complaint clustering and auditable incident intelligence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "complaint_clusters" not in tables:
        op.create_table(
            "complaint_clusters",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text), sa.Column("category", sa.String(100)),
            sa.Column("status", sa.String(50), server_default="candidate"),
            sa.Column("cluster_score", sa.Float, server_default="0"),
            sa.Column("complaint_count", sa.Integer, server_default="0"),
            sa.Column("first_detected_at", sa.DateTime), sa.Column("last_updated_at", sa.DateTime),
            sa.Column("affected_region", sa.String(255)), sa.Column("affected_product", sa.String(255)),
            sa.Column("severity", sa.String(50), server_default="medium"), sa.Column("confidence", sa.Float, server_default="0"),
            sa.Column("created_at", sa.DateTime), sa.Column("updated_at", sa.DateTime),
        )
    if "cluster_complaints" not in tables:
        op.create_table(
            "cluster_complaints",
            sa.Column("cluster_id", sa.String(36), sa.ForeignKey("complaint_clusters.id"), primary_key=True),
            sa.Column("complaint_id", sa.String(36), sa.ForeignKey("complaints.id"), primary_key=True),
            sa.Column("relationship_score", sa.Float), sa.Column("relationship_reason", sa.JSON),
        )
    if "incident_evidence" not in tables:
        op.create_table(
            "incident_evidence",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
            sa.Column("cluster_id", sa.String(36), sa.ForeignKey("complaint_clusters.id")),
            sa.Column("detection_timestamp", sa.DateTime), sa.Column("complaint_ids", sa.JSON),
            sa.Column("similarity_scores", sa.JSON), sa.Column("signals_used", sa.JSON),
            sa.Column("thresholds", sa.JSON), sa.Column("ai_assessment", sa.JSON),
            sa.Column("confidence", sa.Float), sa.Column("recommended_actions", sa.JSON),
        )
    incident_columns = {column["name"] for column in inspector.get_columns("incidents")}
    additions = {
        "potential_root_cause": sa.Text(), "evidence_summary": sa.Text(), "severity": sa.String(50),
        "high_priority_count": sa.Integer(), "sla_breach_count": sa.Integer(),
        "estimated_business_impact": sa.Float(), "regions_affected": sa.Integer(), "products_affected": sa.Integer(),
        "baseline_volume": sa.Float(), "current_volume": sa.Integer(), "volume_change_percent": sa.Float(),
        "cluster_id": sa.String(36),
    }
    for name, column in additions.items():
        if name not in incident_columns:
            op.add_column("incidents", sa.Column(name, column, sa.ForeignKey("complaint_clusters.id") if name == "cluster_id" else None))


def downgrade() -> None:
    return None
