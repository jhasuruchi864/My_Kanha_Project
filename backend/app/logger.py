"""
Logging Configuration
Uses loguru for structured logging.
"""

import sys
from loguru import logger

from app.config import settings


def setup_logger():
    """Configure the application logger."""
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # Add file handler for production
    if not settings.DEBUG:
        logger.add(
            "logs/kanha_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="zip",
        )

    return logger


# Initialize logger
setup_logger()

__all__ = ["logger"]
