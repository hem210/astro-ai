"""
Logging configuration for the Astro AI application.

Sets up a shared logger named "astro_ai" that writes to both the console
and a persistent log file at logs/app.log (relative to the project root).

Usage:
    from app.logger import get_logger
    logger = get_logger(__name__)
    logger.info("something happened")
"""

import logging
import sys
from pathlib import Path

# Project root is one level above this file (app/)
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "app.log"

_LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOGGER_NAME = "astro_ai"


def setup_logging(level: int = logging.INFO) -> None:
    """
    Initialise the astro_ai logger with a console and file handler.
    Safe to call multiple times — subsequent calls are no-ops.
    """
    logger = logging.getLogger(_LOGGER_NAME)

    # Already configured — skip
    if logger.handlers:
        return

    logger.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler — creates logs/ directory if it doesn't exist
    _LOG_DIR.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent log records from bubbling up to the root logger
    logger.propagate = False


def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    """Return a child logger under the astro_ai namespace."""
    return logging.getLogger(f"{_LOGGER_NAME}.{name}" if name != _LOGGER_NAME else name)
