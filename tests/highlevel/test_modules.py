# tests/highlevel/test_modules.py
# Copyright (c) 2026 Clément RACINET
"""Tests for abb_rws_client_python_rw6.highlevel.modules.

Author: Clement RACINET

All rws/ dependencies are mocked via unittest.mock.AsyncMock — no HTTP
calls are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from abb_rws_client_python_rw6.core.exceptions import RWSHTTPError
from abb_rws_client_python_rw6.highlevel.modules import load_module_safe

_MODULE = "abb_rws_client_python_rw6.highlevel.modules"


def _resp(body: str = "", status: int = 200) -> httpx.Response:
    """Build a minimal httpx.Response with a text body."""
    return httpx.Response(status_code=status, text=body)


@pytest.fixture
def client() -> MagicMock:
    """Return a bare MagicMock acting as RWSClient."""
    return MagicMock()


# ---------------------------------------------------------------------------
# load_module_safe
# ---------------------------------------------------------------------------
# modules.py utilise post_mastership_domain_request / post_mastership_domain_release
# (POST /rw/mastership/{domain}) — signatures : (client, *, domain, action).


class TestLoadModuleSafe:
    """Tests for load_module_safe()."""

    @pytest.mark.asyncio
    async def test_full_sequence_order(self, client: MagicMock) -> None:
        """resetpp → request → unload → load → release."""
        call_order: list[str] = []

        async def fake_reset(c: object, *, action: str) -> httpx.Response:
            call_order.append("resetpp")
            return _resp(status=204)

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:request")
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:release")
            return _resp(status=204)

        async def fake_unload(c: object, *, task: str, action: str, module: str) -> httpx.Response:
            call_order.append("unload")
            return _resp(status=204)

        async def fake_load(
            c: object, *, task: str, action: str, modulepath: str
        ) -> httpx.Response:
            call_order.append("load")
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.reset_rapid_program_pointer_to_main", new=fake_reset),
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(f"{_MODULE}.post_unload_module_from_rapid_task", new=fake_unload),
            patch(f"{_MODULE}.load_rapid_module_into_rapid_task", new=fake_load),
        ):
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/my_mod.mod",
                module_name="my_mod",
            )

        assert call_order == [
            "resetpp",
            "mastership:request",
            "unload",
            "load",
            "mastership:release",
        ]

    @pytest.mark.asyncio
    async def test_unload_error_is_swallowed(self, client: MagicMock) -> None:
        """A 404 on unload must not propagate — module may not be loaded."""
        released: list[bool] = []

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        async def fake_unload_fail(
            c: object, *, task: str, action: str, module: str
        ) -> httpx.Response:
            raise RWSHTTPError("not loaded", status_code=404)

        with (
            patch(
                f"{_MODULE}.reset_rapid_program_pointer_to_main",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(f"{_MODULE}.post_unload_module_from_rapid_task", new=fake_unload_fail),
            patch(
                f"{_MODULE}.load_rapid_module_into_rapid_task",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/my_mod.mod",
                module_name="my_mod",
            )

        assert released == [True]

    @pytest.mark.asyncio
    async def test_release_on_load_failure(self, client: MagicMock) -> None:
        """Mastership must be released even when load raises."""
        released: list[bool] = []

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        with (
            patch(
                f"{_MODULE}.reset_rapid_program_pointer_to_main",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(
                f"{_MODULE}.post_unload_module_from_rapid_task",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.load_rapid_module_into_rapid_task",
                new=AsyncMock(side_effect=RWSHTTPError("load failed", status_code=500)),
            ),
            pytest.raises(RWSHTTPError),
        ):
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/my_mod.mod",
                module_name="my_mod",
            )

        assert released == [True]

    @pytest.mark.asyncio
    async def test_resetpp_failure_is_swallowed(self, client: MagicMock) -> None:
        """resetpp HTTP error must be swallowed (first load, no program)."""
        call_order: list[str] = []

        async def fake_reset_fail(c: object, *, action: str) -> httpx.Response:
            raise RWSHTTPError("no program", status_code=400)

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:request")
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:release")
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.reset_rapid_program_pointer_to_main", new=fake_reset_fail),
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(
                f"{_MODULE}.post_unload_module_from_rapid_task",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.load_rapid_module_into_rapid_task",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/my_mod.mod",
                module_name="my_mod",
            )

        assert call_order == ["mastership:request", "mastership:release"]

    @pytest.mark.asyncio
    async def test_load_called_with_correct_args(self, client: MagicMock) -> None:
        """load_rapid_module_into_rapid_task must receive the correct args."""
        mock_load = AsyncMock(return_value=_resp(status=204))
        with (
            patch(
                f"{_MODULE}.reset_rapid_program_pointer_to_main",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_unload_module_from_rapid_task",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.load_rapid_module_into_rapid_task", new=mock_load),
        ):
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/LoadModule.mod",
                module_name="LoadModule",
            )

        mock_load.assert_awaited_once_with(
            client,
            task="T_ROB1",
            action="loadmod",
            modulepath="$HOME/LoadModule.mod",
        )
