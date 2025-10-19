"""
Logging configuration for golf2025 application.

Provides centralized logging setup with different loggers for
different parts of the application.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
    enable_file_logging: bool = True
) -> None:
    """
    Configure application logging.

    Args:
        log_dir: Directory to store log files (default: project_root/logs)
        level: Logging level (default: INFO)
        enable_file_logging: Whether to log to files (default: True)
    """
    # Create logs directory if it doesn't exist
    if enable_file_logging:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)

    # Base format for all loggers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # File handler (if enabled)
    if enable_file_logging:
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'golf2025.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Pre-configured loggers for different modules
app_logger = logging.getLogger('superb_ock')
media_logger = logging.getLogger('superb_ock.media')
notification_logger = logging.getLogger('superb_ock.notifications')
stats_logger = logging.getLogger('superb_ock.stats')
admin_logger = logging.getLogger('superb_ock.admin')
scoring_logger = logging.getLogger('superb_ock.scoring')
