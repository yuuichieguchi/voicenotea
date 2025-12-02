"""Logging system with three-layer error handling and exit codes."""

import logging
import sys
from pathlib import Path
from typing import Optional


class ConfigError(Exception):
    """Configuration-related error."""

    exit_code = 1


class PathError(Exception):
    """Path validation or file operation error."""

    exit_code = 2


class ProcessingError(Exception):
    """Image processing or transformation error."""

    exit_code = 3


class FatalError(Exception):
    """Unexpected fatal system error."""

    exit_code = 10


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    is_ci: bool = False,
) -> logging.Logger:
    """Configure and return a logger with console and optional file handlers.

    Sets up structured logging with consistent formatting for both console
    and file output. Automatically detects CI environments.

    Args:
        name: Logger name (usually __name__).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO.
        log_file: Optional path to log file. If provided, logs to file as well.
        is_ci: Whether running in CI environment. Affects formatting.

    Returns:
        Configured logger instance.

    Raises:
        ValueError: If level is invalid.

    Examples:
        >>> logger = setup_logger(__name__, level="DEBUG")
        >>> logger.info("Processing started")
        >>> logger.error("An error occurred")

        With file output:
        >>> logger = setup_logger(__name__, log_file=Path("app.log"))
    """
    logger = logging.getLogger(name)

    # Validate level
    try:
        log_level = getattr(logging, level.upper())
    except AttributeError:
        raise ValueError(f"Invalid log level: {level}")

    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Format with context for debugging
    if is_ci:
        fmt = "%(levelname)s: %(message)s"
    else:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(fmt)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        try:
            log_path = Path(log_file) if isinstance(log_file, str) else log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.warning(f"Failed to open log file {log_file}: {e}")

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def log_exception(logger: logging.Logger, exception: Exception) -> int:
    """Log an exception with full context and return exit code.

    Extracts exit code from exception if available, otherwise returns 1.

    Args:
        logger: Logger instance.
        exception: Exception to log.

    Returns:
        Exit code (0-255).

    Examples:
        >>> try:
        ...     raise ConfigError("Invalid configuration")
        ... except Exception as e:
        ...     exit_code = log_exception(logger, e)
    """
    exit_code = getattr(exception, "exit_code", 1)

    if isinstance(exception, (ConfigError, PathError, ProcessingError)):
        logger.error(str(exception))
    elif isinstance(exception, FatalError):
        logger.exception(f"Fatal error: {exception}")
    else:
        logger.exception(f"Unexpected error: {exception}")

    return exit_code
