# tests/highlevel/test_panel.py
# Copyright (c) 2026 Clément RACINET
"""Tests for abb_rws_client_python_rw6.highlevel.panel.

Author: Clement RACINET

All rws/ dependencies are mocked via unittest.mock.AsyncMock — no HTTP
calls are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from abb_rws_client_python_rw6.highlevel.panel import set_motors_off, set_motors_on

_MODULE = "abb_rws_client_python_rw6.highlevel.panel"


def _resp(body: str = "", status: int = 200) -> httpx.Response:
    """Build a minimal httpx.Response with a text body."""
    return httpx.Response(status_code=status, text=body)


@pytest.fixture
def client() -> MagicMock:
    """Return a bare MagicMock acting as RWSClient."""
    return MagicMock()


class TestMotorControl:
    """Tests for set_motors_on() and set_motors_off()."""

    @pytest.mark.asyncio
    async def test_motors_on(self, client: MagicMock) -> None:
        mock_set = AsyncMock(return_value=_resp(status=204))
        with patch(f"{_MODULE}.set_controller_state", new=mock_set):
            await set_motors_on(client)

        mock_set.assert_awaited_once_with(client, action="setctrlstate", ctrl_state="motoron")

    @pytest.mark.asyncio
    async def test_motors_off(self, client: MagicMock) -> None:
        mock_set = AsyncMock(return_value=_resp(status=204))
        with patch(f"{_MODULE}.set_controller_state", new=mock_set):
            await set_motors_off(client)

        mock_set.assert_awaited_once_with(client, action="setctrlstate", ctrl_state="motoroff")

    @pytest.mark.asyncio
    async def test_motors_on_returns_none(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.set_controller_state",
            new=AsyncMock(return_value=_resp(status=204)),
        ):
            result = await set_motors_on(client)
        assert result is None

    @pytest.mark.asyncio
    async def test_motors_off_returns_none(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.set_controller_state",
            new=AsyncMock(return_value=_resp(status=204)),
        ):
            result = await set_motors_off(client)
        assert result is None
