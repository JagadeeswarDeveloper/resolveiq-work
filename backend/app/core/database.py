"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
