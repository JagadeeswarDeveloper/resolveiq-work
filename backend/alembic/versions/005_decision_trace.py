"""Add decision trace persistence for complaint explainability."""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "complaints" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("complaints")]
        if "decision_trace" not in columns:
            op.add_column("complaints", sa.Column("decision_trace", sa.JSON, server_default=sa.text("'[]'")))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "complaints" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("complaints")]
        if "decision_trace" in columns:
            op.drop_column("complaints", "decision_trace")
