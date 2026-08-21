# tests/highlevel/test_execution.py
# Copyright (c) 2026 Clément RACINET
"""Tests for abb_rws_client_python_rw6.highlevel.execution.

Author: Clement RACINET

All rws/ dependencies are mocked via unittest.mock.AsyncMock — no HTTP
calls are made.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from abb_rws_client_python_rw6.highlevel.execution import (
    _parse_exec_state,
    is_running,
    start_rapid,
    stop_rapid,
    wait_until_stopped,
)

_MODULE = "abb_rws_client_python_rw6.highlevel.execution"


def _resp(body: str = "", status: int = 200) -> httpx.Response:
    """Build a minimal httpx.Response with a text body."""
    return httpx.Response(status_code=status, text=body)


def _json_resp(data: dict, status: int = 200) -> httpx.Response:  # type: ignore[type-arg]
    """Build a minimal httpx.Response with a JSON body."""
    return httpx.Response(
        status_code=status,
        content=json.dumps(data).encode(),
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def client() -> MagicMock:
    """Return a bare MagicMock acting as RWSClient."""
    return MagicMock()


class TestParseExecState:
    """Unit tests for the _parse_exec_state helper."""

    def test_json_running(self) -> None:
        assert _parse_exec_state(_json_resp({"state": [{"ctrlexecstate": "running"}]})) == "running"

    def test_json_stopped(self) -> None:
        assert _parse_exec_state(_json_resp({"state": [{"ctrlexecstate": "stopped"}]})) == "stopped"

    def test_xml_running(self) -> None:
        assert _parse_exec_state(_resp('<span class="ctrlexecstate">running</span>')) == "running"

    def test_xml_stopped(self) -> None:
        assert _parse_exec_state(_resp('<span class="ctrlexecstate">stopped</span>')) == "stopped"

    def test_raises_on_unparseable(self) -> None:
        with pytest.raises(ValueError, match="ctrlexecstate"):
            _parse_exec_state(_resp("<html>nothing</html>"))

    def test_xml_fallback_when_json_state_empty(self) -> None:
        """Empty JSON state list must fall through to the XML path."""
        body = '<span class="ctrlexecstate">stopped</span>'
        assert _parse_exec_state(_resp(body)) == "stopped"


class TestIsRunning:
    """Tests for is_running()."""

    @pytest.mark.asyncio
    async def test_true_when_running(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.get_rapid_execution_state",
            new=AsyncMock(return_value=_json_resp({"state": [{"ctrlexecstate": "running"}]})),
        ):
            assert await is_running(client) is True

    @pytest.mark.asyncio
    async def test_false_when_stopped(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.get_rapid_execution_state",
            new=AsyncMock(return_value=_json_resp({"state": [{"ctrlexecstate": "stopped"}]})),
        ):
            assert await is_running(client) is False

    @pytest.mark.asyncio
    async def test_false_when_idle(self, client: MagicMock) -> None:
        """Any state other than 'running' must return False."""
        with patch(
            f"{_MODULE}.get_rapid_execution_state",
            new=AsyncMock(return_value=_json_resp({"state": [{"ctrlexecstate": "idle"}]})),
        ):
            assert await is_running(client) is False


class TestStartRapid:
    """Tests for start_rapid()."""

    @pytest.mark.asyncio
    async def test_calls_resetpp_then_start(self, client: MagicMock) -> None:
        mock_reset = AsyncMock(return_value=_resp(status=204))
        mock_start = AsyncMock(return_value=_resp(status=204))
        with (
            patch(f"{_MODULE}.reset_rapid_program_pointer_to_main", new=mock_reset),
            patch(f"{_MODULE}.start_rapid_execution", new=mock_start),
        ):
            await start_rapid(client)

        mock_reset.assert_awaited_once_with(client, action="resetpp")
        _, kwargs = mock_start.call_args
        assert kwargs["action"] == "start"
        assert kwargs["cycle"] == "forever"

    @pytest.mark.asyncio
    async def test_cycle_once_forwarded(self, client: MagicMock) -> None:
        mock_reset = AsyncMock(return_value=_resp(status=204))
        mock_start = AsyncMock(return_value=_resp(status=204))
        with (
            patch(f"{_MODULE}.reset_rapid_program_pointer_to_main", new=mock_reset),
            patch(f"{_MODULE}.start_rapid_execution", new=mock_start),
        ):
            await start_rapid(client, cycle="once")

        _, kwargs = mock_start.call_args
        assert kwargs["cycle"] == "once"

    @pytest.mark.asyncio
    async def test_default_params_forwarded(self, client: MagicMock) -> None:
        """All default parameters must be forwarded to start_rapid_execution."""
        mock_reset = AsyncMock(return_value=_resp(status=204))
        mock_start = AsyncMock(return_value=_resp(status=204))
        with (
            patch(f"{_MODULE}.reset_rapid_program_pointer_to_main", new=mock_reset),
            patch(f"{_MODULE}.start_rapid_execution", new=mock_start),
        ):
            await start_rapid(client)

        _, kwargs = mock_start.call_args
        assert kwargs["regain"] == "continue"
        assert kwargs["execmode"] == "continue"
        assert kwargs["condition"] == "none"
        assert kwargs["stopatbp"] == "disabled"
        assert kwargs["alltaskbytsp"] == "false"

    @pytest.mark.asyncio
    async def test_resetpp_called_before_start(self, client: MagicMock) -> None:
        """resetpp must be awaited before start_rapid_execution."""
        call_order: list[str] = []

        async def fake_reset(c: object, *, action: str) -> httpx.Response:
            call_order.append("reset")
            return _resp(status=204)

        async def fake_start(c: object, **kwargs: object) -> httpx.Response:
            call_order.append("start")
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.reset_rapid_program_pointer_to_main", new=fake_reset),
            patch(f"{_MODULE}.start_rapid_execution", new=fake_start),
        ):
            await start_rapid(client)

        assert call_order == ["reset", "start"]


class TestStopRapid:
    """Tests for stop_rapid()."""

    @pytest.mark.asyncio
    async def test_calls_stop_execution(self, client: MagicMock) -> None:
        mock_stop = AsyncMock(return_value=_resp(status=204))
        with patch(f"{_MODULE}.stop_rapid_execution", new=mock_stop):
            await stop_rapid(client)

        mock_stop.assert_awaited_once_with(client, action="stop", stopmode="stop")

    @pytest.mark.asyncio
    async def test_custom_stopmode(self, client: MagicMock) -> None:
        mock_stop = AsyncMock(return_value=_resp(status=204))
        with patch(f"{_MODULE}.stop_rapid_execution", new=mock_stop):
            await stop_rapid(client, stopmode="qstop")

        _, kwargs = mock_stop.call_args
        assert kwargs["stopmode"] == "qstop"

    @pytest.mark.asyncio
    async def test_halt_stopmode(self, client: MagicMock) -> None:
        mock_stop = AsyncMock(return_value=_resp(status=204))
        with patch(f"{_MODULE}.stop_rapid_execution", new=mock_stop):
            await stop_rapid(client, stopmode="halt")

        _, kwargs = mock_stop.call_args
        assert kwargs["stopmode"] == "halt"


class TestWaitUntilStopped:
    """Tests for wait_until_stopped()."""

    @pytest.mark.asyncio
    async def test_returns_immediately_when_stopped(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.is_running",
            new=AsyncMock(return_value=False),
        ):
            await wait_until_stopped(client)

    @pytest.mark.asyncio
    async def test_polls_until_stopped(self, client: MagicMock) -> None:
        side_effects = [True, True, False]
        call_count = 0

        async def fake_is_running(_: object) -> bool:
            nonlocal call_count
            result = side_effects[call_count]
            call_count += 1
            return result

        with (
            patch(f"{_MODULE}.is_running", new=fake_is_running),
            patch("asyncio.sleep", new=AsyncMock()),
        ):
            await wait_until_stopped(client, poll_interval=0.01)

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_timeout(self, client: MagicMock) -> None:
        with (
            patch(
                f"{_MODULE}.is_running",
                new=AsyncMock(return_value=True),
            ),
            patch("asyncio.sleep", new=AsyncMock()),
            pytest.raises(TimeoutError, match="RAPID still running"),
        ):
            await wait_until_stopped(client, poll_interval=0.1, timeout=0.05)

    @pytest.mark.asyncio
    async def test_no_timeout_polls_forever_until_stopped(self, client: MagicMock) -> None:
        """With timeout=None, must keep polling until stopped."""
        side_effects = [True] * 5 + [False]
        call_count = 0

        async def fake_is_running(_: object) -> bool:
            nonlocal call_count
            result = side_effects[call_count]
            call_count += 1
            return result

        with (
            patch(f"{_MODULE}.is_running", new=fake_is_running),
            patch("asyncio.sleep", new=AsyncMock()),
        ):
            await wait_until_stopped(client, poll_interval=0.01, timeout=None)

        assert call_count == 6
