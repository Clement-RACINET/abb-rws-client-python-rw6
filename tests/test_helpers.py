# tests/test_helpers.py
"""
Tests unitaires pour helpers.py.

Stratégie : mock des fonctions sous-jacentes (execution.py, rapid_variable.py)
via unittest.mock.AsyncMock — pas de mock HTTP direct.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from old_abb_rws_client.exceptions import RWSTimeoutError
from old_abb_rws_client.execution import ExecutionState
from old_abb_rws_client.helpers import (
    DEFAULT_POLL_INTERVAL_S,
    DEFAULT_TIMEOUT_S,
    reset_and_start,
    wait_for_var,
    wait_until_stopped,
)


# ---------------------------------------------------------------------------
# Fixture client mock minimal
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> AsyncMock:
    """Client mock minimal — les appels HTTP sont mockés au niveau des fonctions."""
    return AsyncMock()


# ---------------------------------------------------------------------------
# reset_and_start
# ---------------------------------------------------------------------------


class TestResetAndStart:
    async def test_calls_reset_then_start(self, mock_client: AsyncMock) -> None:
        call_order: list[str] = []

        async def fake_reset_pp(client):  # type: ignore[no-untyped-def]
            call_order.append("reset_pp")

        async def fake_start(client, **kwargs):  # type: ignore[no-untyped-def]
            call_order.append("start_execution")

        with (
            patch("abb_rws_client.helpers.reset_pp", side_effect=fake_reset_pp),
            patch("abb_rws_client.helpers.start_execution", side_effect=fake_start),
            patch("abb_rws_client.helpers.Mastership") as mock_mastership,
        ):
            mock_mastership.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_mastership.return_value.__aexit__ = AsyncMock(return_value=False)
            await reset_and_start(mock_client)

        assert call_order == ["reset_pp", "start_execution"]

    async def test_start_called_with_defaults(self, mock_client: AsyncMock) -> None:
        captured: dict = {}

        async def fake_start(client, **kwargs):  # type: ignore[no-untyped-def]
            captured.update(kwargs)

        with (
            patch("abb_rws_client.helpers.reset_pp", new_callable=AsyncMock),
            patch("abb_rws_client.helpers.start_execution", side_effect=fake_start),
            patch("abb_rws_client.helpers.Mastership") as mock_mastership,
        ):
            mock_mastership.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_mastership.return_value.__aexit__ = AsyncMock(return_value=False)
            await reset_and_start(mock_client)

        assert captured["cycle"] == "once"
        assert captured["execmode"] == "continue"

    async def test_start_called_with_custom_cycle(self, mock_client: AsyncMock) -> None:
        captured: dict = {}

        async def fake_start(client, **kwargs):  # type: ignore[no-untyped-def]
            captured.update(kwargs)

        with (
            patch("abb_rws_client.helpers.reset_pp", new_callable=AsyncMock),
            patch("abb_rws_client.helpers.start_execution", side_effect=fake_start),
            patch("abb_rws_client.helpers.Mastership") as mock_mastership,
        ):
            mock_mastership.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_mastership.return_value.__aexit__ = AsyncMock(return_value=False)
            await reset_and_start(mock_client, cycle="forever")

        assert captured["cycle"] == "forever"


# ---------------------------------------------------------------------------
# wait_until_stopped
# ---------------------------------------------------------------------------


class TestWaitUntilStopped:
    async def test_returns_immediately_if_stopped(self, mock_client: AsyncMock) -> None:
        stopped = ExecutionState(ctrlexecstate="stopped", cycle="once", excstate="stopped")
        with patch(
            "abb_rws_client.helpers.get_execution_state",
            new_callable=AsyncMock,
            return_value=stopped,
        ):
            await wait_until_stopped(mock_client, timeout_s=5.0)

    async def test_polls_until_stopped(self, mock_client: AsyncMock) -> None:
        running = ExecutionState(ctrlexecstate="running", cycle="once", excstate="running")
        stopped = ExecutionState(ctrlexecstate="stopped", cycle="once", excstate="stopped")
        responses = [running, running, stopped]

        with (
            patch(
                "abb_rws_client.helpers.get_execution_state",
                new_callable=AsyncMock,
                side_effect=responses,
            ),
            patch("abb_rws_client.helpers.asyncio.sleep", new_callable=AsyncMock),
        ):
            await wait_until_stopped(mock_client, timeout_s=5.0, poll_interval_s=0.1)

    async def test_raises_timeout(self, mock_client: AsyncMock) -> None:
        running = ExecutionState(ctrlexecstate="running", cycle="once", excstate="running")
        with (
            patch(
                "abb_rws_client.helpers.get_execution_state",
                new_callable=AsyncMock,
                return_value=running,
            ),
            patch("abb_rws_client.helpers.asyncio.sleep", new_callable=AsyncMock),
        ):
            with pytest.raises(RWSTimeoutError, match="wait_until_stopped"):
                await wait_until_stopped(
                    mock_client, timeout_s=0.3, poll_interval_s=0.1
                )

    def test_default_constants(self) -> None:
        assert DEFAULT_TIMEOUT_S == 30.0
        assert DEFAULT_POLL_INTERVAL_S == 0.2


# ---------------------------------------------------------------------------
# wait_for_var
# ---------------------------------------------------------------------------


class TestWaitForVar:
    async def test_returns_immediately_if_match(self, mock_client: AsyncMock) -> None:
        with patch(
            "abb_rws_client.helpers.get_rapid_var",
            new_callable=AsyncMock,
            return_value=True,
        ):
            await wait_for_var(
                mock_client, "READY", "bool", True,
                module="MYMOD", timeout_s=5.0,
            )

    async def test_polls_until_match(self, mock_client: AsyncMock) -> None:
        with (
            patch(
                "abb_rws_client.helpers.get_rapid_var",
                new_callable=AsyncMock,
                side_effect=[False, False, True],
            ),
            patch("abb_rws_client.helpers.asyncio.sleep", new_callable=AsyncMock),
        ):
            await wait_for_var(
                mock_client, "READY", "bool", True,
                module="MYMOD", timeout_s=5.0, poll_interval_s=0.1,
            )

    async def test_raises_timeout(self, mock_client: AsyncMock) -> None:
        with (
            patch(
                "abb_rws_client.helpers.get_rapid_var",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("abb_rws_client.helpers.asyncio.sleep", new_callable=AsyncMock),
        ):
            with pytest.raises(RWSTimeoutError, match="READY"):
                await wait_for_var(
                    mock_client, "READY", "bool", True,
                    module="MYMOD", timeout_s=0.3, poll_interval_s=0.1,
                )

    async def test_passes_module_and_task(self, mock_client: AsyncMock) -> None:
        """Vérifie que module et task sont bien transmis à get_rapid_var."""
        captured: dict = {}

        async def fake_get(client, var, rapid_type, **kwargs):  # type: ignore[no-untyped-def]
            captured.update(kwargs)
            return 42.0

        with patch("abb_rws_client.helpers.get_rapid_var", side_effect=fake_get):
            await wait_for_var(
                mock_client, "COUNTER", "num", 42.0,
                module="MYMOD", task="T_ROB2", timeout_s=5.0,
            )

        assert captured["module"] == "MYMOD"
        assert captured["task"] == "T_ROB2"
