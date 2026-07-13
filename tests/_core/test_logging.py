# tests/_core/test_logging.py
"""Tests for abb_rws_client._core.logging."""

from __future__ import annotations

from collections.abc import Generator
import io
import logging

import pytest

from abb_rws_client._core.logging import (
    _ROOT_LOGGER_NAME,
    configure_logging,
    get_logger,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_lib_logger() -> Generator[None, None, None]:
    """Restore the library root logger to a clean state after each test.

    Prevents handler accumulation across tests.
    """
    yield
    lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
    lib_logger.handlers.clear()
    lib_logger.setLevel(logging.WARNING)
    lib_logger.propagate = False


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def test_returns_logger_instance(self) -> None:
        result = configure_logging(level="WARNING")
        assert isinstance(result, logging.Logger)
        assert result.name == _ROOT_LOGGER_NAME

    def test_sets_level_from_string(self) -> None:
        configure_logging(level="DEBUG")
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.level == logging.DEBUG

    def test_sets_level_from_int(self) -> None:
        configure_logging(level=logging.ERROR)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.level == logging.ERROR

    def test_level_string_case_insensitive(self) -> None:
        configure_logging(level="info")
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.level == logging.INFO

    def test_raises_on_unknown_level_string(self) -> None:
        with pytest.raises(ValueError, match="Unknown logging level"):
            configure_logging(level="VERBOSE")

    def test_installs_stream_handler_by_default(self) -> None:
        stream = io.StringIO()
        configure_logging(level="DEBUG", stream=stream)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert len(lib_logger.handlers) == 1
        assert isinstance(lib_logger.handlers[0], logging.StreamHandler)

    def test_replaces_handlers_on_second_call(self) -> None:
        configure_logging(level="DEBUG")
        configure_logging(level="INFO")
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert len(lib_logger.handlers) == 1

    def test_propagate_is_false(self) -> None:
        configure_logging(level="DEBUG")
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.propagate is False

    def test_custom_handler_is_used(self) -> None:
        stream = io.StringIO()
        custom_handler = logging.StreamHandler(stream)
        configure_logging(level="DEBUG", handler=custom_handler)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.handlers[0] is custom_handler

    def test_message_written_to_stream(self) -> None:
        stream = io.StringIO()
        configure_logging(level="DEBUG", stream=stream)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        lib_logger.debug("hello test")
        output = stream.getvalue()
        assert "hello test" in output

    def test_message_not_written_when_below_level(self) -> None:
        stream = io.StringIO()
        configure_logging(level="ERROR", stream=stream)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        lib_logger.debug("should not appear")
        lib_logger.info("should not appear either")
        assert stream.getvalue() == ""

    def test_custom_fmt_applied(self) -> None:
        stream = io.StringIO()
        configure_logging(level="DEBUG", fmt="CUSTOM %(message)s", stream=stream)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        lib_logger.debug("marker")
        assert "CUSTOM marker" in stream.getvalue()

    def test_default_level_is_warning(self) -> None:
        configure_logging()
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.level == logging.WARNING

    @pytest.mark.parametrize(
        "level_str,expected",
        [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ],
    )
    def test_all_standard_levels(self, level_str: str, expected: int) -> None:
        configure_logging(level=level_str)
        lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)
        assert lib_logger.level == expected


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_logger_instance(self) -> None:
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_name_is_prefixed(self) -> None:
        logger = get_logger("mymodule")
        assert logger.name == f"{_ROOT_LOGGER_NAME}.mymodule"

    def test_dunder_name_pattern(self) -> None:
        """Typical usage: get_logger(__name__)."""
        logger = get_logger("abb_rws_client._core.env")
        assert logger.name == f"{_ROOT_LOGGER_NAME}.abb_rws_client._core.env"

    def test_child_inherits_parent_level(self) -> None:
        """Child logger must inherit the root library logger's level."""
        configure_logging(level="DEBUG")
        child = get_logger("child.test")
        # Child has no level set itself — effective level comes from parent
        assert child.getEffectiveLevel() == logging.DEBUG

    def test_different_names_return_different_loggers(self) -> None:
        logger_a = get_logger("module_a")
        logger_b = get_logger("module_b")
        assert logger_a is not logger_b
        assert logger_a.name != logger_b.name

    def test_same_name_returns_same_instance(self) -> None:
        """logging.getLogger is a registry — same name = same object."""
        logger_a = get_logger("singleton")
        logger_b = get_logger("singleton")
        assert logger_a is logger_b
