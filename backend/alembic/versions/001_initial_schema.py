"""Create the complete ResolveIQ schema."""

from alembic import op
from app.core.database import Base
from app import models  # noqa: F401 - register all ORM tables with Base.metadata


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create every table and association defined by the ORM."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop every table created by this revision."""
    Base.metadata.drop_all(bind=op.get_bind())
