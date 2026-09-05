"""Compatibility revision retained for existing Alembic history."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    """All current phase-2 tables are created by the initial schema."""
    # Revision 001 is metadata-backed for clean installs. These guards upgrade
    # databases created by earlier Phase 2 revisions without duplicating columns.
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    document_columns = {column["name"] for column in inspector.get_columns("knowledge_documents")}
    recommendation_columns = {column["name"] for column in inspector.get_columns("resolution_recommendations")}
    if "status" not in document_columns:
        op.add_column("knowledge_documents", sa.Column("status", sa.String(50), server_default="draft"))
    if "source" not in document_columns:
        op.add_column("knowledge_documents", sa.Column("source", sa.String(255), server_default="ResolveIQ demo policy"))
    if "policy_evidence" not in recommendation_columns:
        op.add_column("resolution_recommendations", sa.Column("policy_evidence", postgresql.JSONB(), nullable=True))
    if "policy_confidence" not in recommendation_columns:
        op.add_column("resolution_recommendations", sa.Column("policy_confidence", sa.Float(), server_default="0"))


def downgrade():
    """No-op compatibility downgrade."""
    return None
