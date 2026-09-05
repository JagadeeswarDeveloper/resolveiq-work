"""Logging configuration."""

import logging
import json
from datetime import datetime

from app.core.config import settings


def setup_logging():
    """Configure structured logging."""
    log_level = getattr(logging, settings.log_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
