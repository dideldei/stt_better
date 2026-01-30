"""
Logging setup for STT-Diktat-Agent.

Configures file-based logging to data/logs/app.log.
Ensures no PHI (Protected Health Information) is logged.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: Path | None = None) -> None:
    """
    Set up logging to file and optionally console.
    
    Log file: data/logs/app.log
    Format: timestamp, level, message
    No PHI (no audio samples, no transcript text)
    
    Args:
        log_dir: Directory for log file. If None, uses project_root/data/logs/
    """
    if log_dir is None:
        # Assume data/logs/ is relative to project root
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "data" / "logs"
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    
    # Format: timestamp, level, message
    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    root_logger.addHandler(file_handler)
    
    # Optional: Console handler for development (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        fmt="[%(levelname)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log that logging is set up (but don't log PHI)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
