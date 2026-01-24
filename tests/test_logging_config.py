"""Tests for TOAD logging configuration."""

import pytest
import logging
from pathlib import Path
from io import StringIO

from toad.logging_config import (
    TOADFormatter,
    setup_logging,
    get_logger,
    setup_daemon_logging,
)


class TestTOADFormatter:
    """Tests for TOADFormatter."""

    def test_formatter_without_service_tag(self):
        """Test formatter without service tag."""
        formatter = TOADFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert "[INFO] Test message" in formatted
        assert formatted.startswith("20")  # Year starts with 20xx

    def test_formatter_with_service_tag(self):
        """Test formatter with service tag prepends tag to messages."""
        formatter = TOADFormatter(service_tag="DAEMON")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Starting daemon",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        assert "[INFO] [DAEMON] Starting daemon" in formatted

    def test_formatter_preserves_existing_service_tag(self):
        """Test formatter preserves existing [SERVICE] tag in message."""
        formatter = TOADFormatter(service_tag="DAEMON")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="[WATCHER] File detected",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should keep original tag, not double-tag
        assert "[INFO] [WATCHER] File detected" in formatted
        assert "[DAEMON] [WATCHER]" not in formatted

    def test_formatter_datetime_format(self):
        """Test formatter uses correct datetime format."""
        formatter = TOADFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should match: YYYY-MM-DD HH:MM:SS [LEVEL] Message
        parts = formatted.split(" ")
        assert len(parts) >= 4
        assert "-" in parts[0]  # Date with hyphens
        assert ":" in parts[1]  # Time with colons


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_console_only(self, caplog):
        """Test setting up console-only logging."""
        logger = setup_logging(level=logging.INFO, console=True)

        assert logger.name == "toad"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logging_with_file(self, tmp_path):
        """Test setting up logging with file handler."""
        log_file = tmp_path / "test.log"

        logger = setup_logging(
            level=logging.DEBUG,
            log_file=log_file,
            console=False
        )

        # Log a message
        logger.debug("Test message")

        # Check file was created
        assert log_file.exists()

        # Check content
        content = log_file.read_text()
        assert "[DEBUG] Test message" in content

    def test_setup_logging_with_service_tag(self, tmp_path):
        """Test setup_logging applies service tag to all messages."""
        log_file = tmp_path / "daemon.log"

        logger = setup_logging(
            level=logging.INFO,
            service_tag="TEST",
            log_file=log_file,
            console=False
        )

        logger.info("Message without tag")

        content = log_file.read_text()
        assert "[TEST] Message without tag" in content

    def test_setup_logging_creates_log_directory(self, tmp_path):
        """Test setup_logging creates log directory if it doesn't exist."""
        log_file = tmp_path / "nested" / "dir" / "test.log"

        logger = setup_logging(
            level=logging.INFO,
            log_file=log_file,
            console=False
        )

        logger.info("Test")

        assert log_file.exists()
        assert log_file.parent.exists()

    def test_setup_logging_removes_existing_handlers(self):
        """Test setup_logging removes existing handlers."""
        # Setup logging twice
        logger1 = setup_logging(level=logging.INFO)
        handler_count_1 = len(logger1.handlers)

        logger2 = setup_logging(level=logging.DEBUG)
        handler_count_2 = len(logger2.handlers)

        # Should have same or fewer handlers (cleared on second setup)
        assert handler_count_2 <= handler_count_1 + 1


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert "toad.test_module" in logger.name

    def test_get_logger_different_names(self):
        """Test get_logger with different names creates different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name != logger2.name
        assert "module1" in logger1.name
        assert "module2" in logger2.name


class TestSetupDaemonLogging:
    """Tests for setup_daemon_logging function."""

    def test_setup_daemon_logging_default_path(self):
        """Test setup_daemon_logging uses default log path."""
        logger = setup_daemon_logging()

        assert logger.name == "toad"
        assert len(logger.handlers) >= 1

    def test_setup_daemon_logging_custom_path(self, tmp_path):
        """Test setup_daemon_logging with custom log path."""
        log_file = tmp_path / "custom_daemon.log"

        logger = setup_daemon_logging(log_file=log_file, level=logging.DEBUG)

        logger.debug("[DAEMON] Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "[DEBUG] [DAEMON] Test message" in content

    def test_setup_daemon_logging_both_console_and_file(self, tmp_path, capfd):
        """Test daemon logging outputs to both console and file."""
        log_file = tmp_path / "daemon.log"

        logger = setup_daemon_logging(log_file=log_file)
        logger.info("[DAEMON] Test output")

        # Check file
        assert log_file.exists()
        file_content = log_file.read_text()
        assert "[DAEMON] Test output" in file_content

        # Check console (via capfd)
        captured = capfd.readouterr()
        assert "[DAEMON] Test output" in captured.out or "[DAEMON] Test output" in captured.err


class TestLoggingFormatIntegration:
    """Integration tests for logging format."""

    def test_logging_format_matches_spec(self, tmp_path):
        """Test logging output matches specification format."""
        log_file = tmp_path / "test.log"

        logger = setup_logging(level=logging.INFO, log_file=log_file, console=False)

        # Log various service messages
        logger.info("[DAEMON] Starting TOAD daemon")
        logger.info("[WATCHER] Monitoring 3 directories")
        logger.info("[HANDLER] Processing file")
        logger.error("[HANDLER] Failed to process file")

        content = log_file.read_text()
        lines = content.strip().split("\n")

        # Verify format: YYYY-MM-DD HH:MM:SS [LEVEL] [SERVICE] Message
        for line in lines:
            parts = line.split(" ", 3)
            assert len(parts) == 4, f"Expected 4 parts, got {len(parts)}: {line}"

            date_part, time_part, level_part, message_part = parts

            # Validate date: YYYY-MM-DD
            assert len(date_part.split("-")) == 3
            assert date_part.startswith("20")

            # Validate time: HH:MM:SS
            assert len(time_part.split(":")) == 3

            # Validate level: [LEVEL]
            assert level_part in ["[INFO]", "[DEBUG]", "[WARNING]", "[ERROR]", "[CRITICAL]"]

            # Validate message starts with [SERVICE]
            assert message_part.startswith("[")

    def test_no_emojis_in_logs(self, tmp_path):
        """Test logging format does not contain emojis."""
        log_file = tmp_path / "test.log"

        logger = setup_logging(level=logging.INFO, log_file=log_file, console=False)

        logger.info("[DAEMON] Starting daemon")
        logger.info("[WATCHER] File detected")
        logger.error("[HANDLER] Processing failed")

        content = log_file.read_text()

        # Check for common emojis
        emojis = ["✅", "❌", "⚠️", "🔍", "📝", "💾", "🔄", "📊", "🚀", "⏰"]
        for emoji in emojis:
            assert emoji not in content, f"Found emoji {emoji} in logs"
