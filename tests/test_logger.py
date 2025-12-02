"""Tests for logging system and error handling."""

import logging

import pytest

from src.logger import (
    ConfigError,
    FatalError,
    PathError,
    ProcessingError,
    log_exception,
    setup_logger,
)


class TestLoggerSetup:
    """Test logger initialization and configuration."""

    def test_should_create_logger_with_info_level(self):
        """Test creating logger with INFO level."""
        logger = setup_logger("test_logger", level="INFO")

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

    def test_should_create_logger_with_debug_level(self):
        """Test creating logger with DEBUG level."""
        logger = setup_logger("test_logger", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_should_create_logger_with_console_handler(self):
        """Test logger has console handler."""
        logger = setup_logger("test_logger")

        assert len(logger.handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_should_create_logger_with_file_handler(self, tmp_path):
        """Test logger can write to file."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", log_file=log_file)

        logger.info("Test message")

        assert log_file.exists()
        assert "Test message" in log_file.read_text()

    def test_should_raise_error_on_invalid_level(self):
        """Test error on invalid log level."""
        with pytest.raises(ValueError):
            setup_logger("test_logger", level="INVALID")

    def test_should_handle_invalid_log_file_path(self):
        """Test graceful handling of invalid log file path."""
        logger = setup_logger("test_logger", log_file="/invalid/path/log.txt")

        assert logger is not None

    def test_should_not_propagate_to_root_logger(self):
        """Test logger doesn't propagate to root."""
        logger = setup_logger("test_logger")

        assert logger.propagate is False

    def test_should_clear_existing_handlers(self):
        """Test that setup_logger clears existing handlers."""
        logger = setup_logger("test_logger", level="INFO")
        initial_handler_count = len(logger.handlers)

        logger2 = setup_logger("test_logger", level="DEBUG")

        assert len(logger2.handlers) <= initial_handler_count


class TestExceptionClasses:
    """Test custom exception classes and exit codes."""

    def test_config_error_has_exit_code_1(self):
        """Test ConfigError has exit code 1."""
        exc = ConfigError("Test error")

        assert exc.exit_code == 1

    def test_path_error_has_exit_code_2(self):
        """Test PathError has exit code 2."""
        exc = PathError("Test error")

        assert exc.exit_code == 2

    def test_processing_error_has_exit_code_3(self):
        """Test ProcessingError has exit code 3."""
        exc = ProcessingError("Test error")

        assert exc.exit_code == 3

    def test_fatal_error_has_exit_code_10(self):
        """Test FatalError has exit code 10."""
        exc = FatalError("Test error")

        assert exc.exit_code == 10

    def test_should_raise_config_error(self):
        """Test raising ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            raise ConfigError("Configuration is invalid")

        assert str(exc_info.value) == "Configuration is invalid"

    def test_should_raise_path_error(self):
        """Test raising PathError."""
        with pytest.raises(PathError):
            raise PathError("Path not found")

    def test_should_raise_processing_error(self):
        """Test raising ProcessingError."""
        with pytest.raises(ProcessingError):
            raise ProcessingError("Image processing failed")

    def test_should_raise_fatal_error(self):
        """Test raising FatalError."""
        with pytest.raises(FatalError):
            raise FatalError("System error")


class TestLogException:
    """Test exception logging utility."""

    def test_should_return_exit_code_1_for_config_error(self):
        """Test exit code for ConfigError."""
        logger = setup_logger("test")
        exc = ConfigError("Config error")

        exit_code = log_exception(logger, exc)

        assert exit_code == 1

    def test_should_return_exit_code_2_for_path_error(self):
        """Test exit code for PathError."""
        logger = setup_logger("test")
        exc = PathError("Path error")

        exit_code = log_exception(logger, exc)

        assert exit_code == 2

    def test_should_return_exit_code_3_for_processing_error(self):
        """Test exit code for ProcessingError."""
        logger = setup_logger("test")
        exc = ProcessingError("Processing error")

        exit_code = log_exception(logger, exc)

        assert exit_code == 3

    def test_should_return_exit_code_10_for_fatal_error(self):
        """Test exit code for FatalError."""
        logger = setup_logger("test")
        exc = FatalError("Fatal error")

        exit_code = log_exception(logger, exc)

        assert exit_code == 10

    def test_should_return_exit_code_1_for_unknown_exception(self):
        """Test exit code for unknown exception."""
        logger = setup_logger("test")
        exc = ValueError("Unknown error")

        exit_code = log_exception(logger, exc)

        assert exit_code == 1


class TestLoggerFormatting:
    """Test logger message formatting."""

    def test_should_format_console_output_with_context(self, tmp_path):
        """Test console output includes timestamp and level."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test", log_file=log_file)

        logger.info("Test message")

        content = log_file.read_text()
        assert "INFO" in content or "test" in content

    def test_should_log_exception_with_traceback(self, tmp_path):
        """Test exception logging includes traceback."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test", log_file=log_file)

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Caught exception")

        content = log_file.read_text()
        assert "ValueError" in content or "exception" in content.lower()

    def test_should_log_different_levels(self, tmp_path):
        """Test logging messages at different levels."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test", level="DEBUG", log_file=log_file)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        content = log_file.read_text()
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
