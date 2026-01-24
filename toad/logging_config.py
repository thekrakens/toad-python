"""Centralized logging configuration for TOAD.

Provides consistent logging format across all modules:
YYYY-MM-DD HH:MM:SS [LEVEL] [SERVICE] Message
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class TOADFormatter(logging.Formatter):
    """Custom formatter for TOAD logs with [SERVICE] tags."""

    def __init__(self, service_tag: Optional[str] = None):
        """
        Initialize formatter.

        Args:
            service_tag: Optional service tag to prepend to all messages (e.g., "DAEMON")
        """
        self.service_tag = service_tag
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def format(self, record):
        """Format log record with service tag if provided."""
        # Extract [SERVICE] tag from message if present
        message = record.getMessage()

        # If message doesn't have a tag and service_tag is set, prepend it
        if self.service_tag and not message.startswith("["):
            record.msg = f"[{self.service_tag}] {message}"
            record.args = ()

        return super().format(record)


def setup_logging(
    level: int = logging.INFO,
    service_tag: Optional[str] = None,
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for TOAD.

    Args:
        level: Logging level (default: INFO)
        service_tag: Optional service tag for all messages
        log_file: Optional file path for logging
        console: Whether to log to console (default: True)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(level=logging.DEBUG, service_tag="DAEMON")
        >>> logger.info("Starting daemon")  # Output: 2026-01-23 21:45:24 [INFO] [DAEMON] Starting daemon
    """
    logger = logging.getLogger("toad")
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = TOADFormatter(service_tag=service_tag)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("[HANDLER] Processing file")  # Include [SERVICE] tag in message
    """
    return logging.getLogger(f"toad.{name}")


def setup_daemon_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup logging specifically for daemon.

    Args:
        log_file: Path to daemon log file (default: ~/.toad/daemon.log)
        level: Logging level

    Returns:
        Configured daemon logger
    """
    if log_file is None:
        log_file = Path.home() / ".toad" / "daemon.log"

    return setup_logging(
        level=level,
        service_tag=None,  # Services use their own tags
        log_file=log_file,
        console=True
    )
