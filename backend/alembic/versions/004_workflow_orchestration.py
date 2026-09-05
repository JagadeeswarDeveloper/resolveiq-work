"""Add durable complaint workflow checkpoints and events."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "workflow_runs" not in tables:
        op.create_table(
            "workflow_runs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("complaint_id", sa.String(36), sa.ForeignKey("complaints.id"), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="running"),
            sa.Column("current_node", sa.String(50), nullable=False, server_default="CAPTURE"),
            sa.Column("state", sa.JSON),
            sa.Column("retry_count", sa.Integer, server_default="0"),
            sa.Column("last_error", sa.Text),
            sa.Column("created_at", sa.DateTime),
            sa.Column("updated_at", sa.DateTime),
        )
        op.create_index("idx_workflow_run_complaint_status", "workflow_runs", ["complaint_id", "status"])
    if "workflow_events" not in tables:
        op.create_table(
            "workflow_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("workflow_id", sa.String(36), sa.ForeignKey("workflow_runs.id"), nullable=False),
            sa.Column("complaint_id", sa.String(36), sa.ForeignKey("complaints.id"), nullable=False),
            sa.Column("node", sa.String(50), nullable=False),
            sa.Column("arc_stage", sa.String(50), nullable=False),
            sa.Column("agent_or_tool", sa.String(255)),
            sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
            sa.Column("duration_ms", sa.Integer),
            sa.Column("output_summary", sa.JSON),
            sa.Column("error", sa.Text),
            sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
            sa.Column("timestamp", sa.DateTime),
        )


def downgrade() -> None:
    op.drop_table("workflow_events")
    op.drop_index("idx_workflow_run_complaint_status", table_name="workflow_runs")
    op.drop_table("workflow_runs")