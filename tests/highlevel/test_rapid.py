# tests/highlevel/test_rapid.py
"""Tests for abb_rws_client.highlevel.rapid."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from abb_rws_client._core.exceptions import RWSHTTPError
from abb_rws_client.highlevel.rapid import (
    _parse_exec_state,
    _parse_symbol_value,
    get_variable,
    is_running,
    load_module_safe,
    set_motors_off,
    set_motors_on,
    set_variable_with_mastership,
    start_rapid,
    stop_rapid,
    wait_until_stopped,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resp(body: str = "", status: int = 200) -> httpx.Response:
    return httpx.Response(status_code=status, text=body)


def _json_resp(data: dict, status: int = 200) -> httpx.Response:  # type: ignore[type-arg]
    return httpx.Response(
        status_code=status,
        content=json.dumps(data).encode(),
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def client() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# _parse_exec_state
# ---------------------------------------------------------------------------


class TestParseExecState:
    def test_json_running(self) -> None:
        assert _parse_exec_state(
            _json_resp({"state": [{"ctrlexecstate": "running"}]})
        ) == "running"

    def test_json_stopped(self) -> None:
        assert _parse_exec_state(
            _json_resp({"state": [{"ctrlexecstate": "stopped"}]})
        ) == "stopped"

    def test_xml_running(self) -> None:
        assert _parse_exec_state(
            _resp('<span class="ctrlexecstate">running</span>')
        ) == "running"

    def test_xml_stopped(self) -> None:
        assert _parse_exec_state(
            _resp('<span class="ctrlexecstate">stopped</span>')
        ) == "stopped"

    def test_raises_on_unparseable(self) -> None:
        with pytest.raises(ValueError, match="ctrlexecstate"):
            _parse_exec_state(_resp("<html>nothing</html>"))


# ---------------------------------------------------------------------------
# _parse_symbol_value
# ---------------------------------------------------------------------------


class TestParseSymbolValue:
    def test_json_value(self) -> None:
        assert _parse_symbol_value(
            _json_resp({"state": [{"value": "42"}]})
        ) == "42"

    def test_xml_value(self) -> None:
        assert _parse_symbol_value(
            _resp('<span class="value">TRUE</span>')
        ) == "TRUE"

    def test_raises_on_unparseable(self) -> None:
        with pytest.raises(ValueError, match="symbol value"):
            _parse_symbol_value(_resp("<html></html>"))


# ---------------------------------------------------------------------------
# is_running
# ---------------------------------------------------------------------------


class TestIsRunning:
    @pytest.mark.asyncio
    async def test_true_when_running(self, client: MagicMock) -> None:
        with patch(
            "abb_rws_client.highlevel.rapid.get_rapid_execution_state",
            new=AsyncMock(
                return_value=_json_resp({"state": [{"ctrlexecstate": "running"}]})
            ),
        ):
            assert await is_running(client) is True

    @pytest.mark.asyncio
    async def test_false_when_stopped(self, client: MagicMock) -> None:
        with patch(
            "abb_rws_client.highlevel.rapid.get_rapid_execution_state",
            new=AsyncMock(
                return_value=_json_resp({"state": [{"ctrlexecstate": "stopped"}]})
            ),
        ):
            assert await is_running(client) is False


# ---------------------------------------------------------------------------
# start_rapid
# ---------------------------------------------------------------------------


class TestStartRapid:
    @pytest.mark.asyncio
    async def test_calls_resetpp_then_start(self, client: MagicMock) -> None:
        mock_reset = AsyncMock(return_value=_resp(status=204))
        mock_start = AsyncMock(return_value=_resp(status=204))
        with (
            patch(
                "abb_rws_client.highlevel.rapid.reset_rapid_program_pointer_to_main",
                new=mock_reset,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.start_rapid_execution",
                new=mock_start,
            ),
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
            patch(
                "abb_rws_client.highlevel.rapid.reset_rapid_program_pointer_to_main",
                new=mock_reset,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.start_rapid_execution",
                new=mock_start,
            ),
        ):
            await start_rapid(client, cycle="once")

        _, kwargs = mock_start.call_args
        assert kwargs["cycle"] == "once"


# ---------------------------------------------------------------------------
# stop_rapid
# ---------------------------------------------------------------------------


class TestStopRapid:
    @pytest.mark.asyncio
    async def test_calls_stop_execution(self, client: MagicMock) -> None:
        mock_stop = AsyncMock(return_value=_resp(status=204))
        with patch(
            "abb_rws_client.highlevel.rapid.stop_rapid_execution",
            new=mock_stop,
        ):
            await stop_rapid(client)

        mock_stop.assert_awaited_once_with(client, action="stop", stopmode="stop")

    @pytest.mark.asyncio
    async def test_custom_stopmode(self, client: MagicMock) -> None:
        mock_stop = AsyncMock(return_value=_resp(status=204))
        with patch(
            "abb_rws_client.highlevel.rapid.stop_rapid_execution",
            new=mock_stop,
        ):
            await stop_rapid(client, stopmode="qstop")

        _, kwargs = mock_stop.call_args
        assert kwargs["stopmode"] == "qstop"


# ---------------------------------------------------------------------------
# wait_until_stopped
# ---------------------------------------------------------------------------


class TestWaitUntilStopped:
    @pytest.mark.asyncio
    async def test_returns_immediately_when_stopped(
        self, client: MagicMock
    ) -> None:
        with patch(
            "abb_rws_client.highlevel.rapid.is_running",
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
            patch(
                "abb_rws_client.highlevel.rapid.is_running",
                new=fake_is_running,
            ),
            patch("asyncio.sleep", new=AsyncMock()),
        ):
            await wait_until_stopped(client, poll_interval=0.01)

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_timeout(self, client: MagicMock) -> None:
        with (
            patch(
                "abb_rws_client.highlevel.rapid.is_running",
                new=AsyncMock(return_value=True),
            ),
            patch("asyncio.sleep", new=AsyncMock()),
            pytest.raises(TimeoutError, match="RAPID still running"),
        ):
            await wait_until_stopped(client, poll_interval=0.1, timeout=0.05)


# ---------------------------------------------------------------------------
# set_variable_with_mastership
# ---------------------------------------------------------------------------


class TestSetVariableWithMastership:
    @pytest.mark.asyncio
    async def test_request_write_release_order(
        self, client: MagicMock
    ) -> None:
        call_order: list[str] = []

        async def fake_mastership(c: object, *, action: str) -> httpx.Response:
            call_order.append(f"mastership:{action}")
            return _resp(status=204)

        async def fake_update(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            call_order.append("update")
            return _resp(status=204)

        with (
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_request",
                new=fake_mastership,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_release",
                new=fake_mastership,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.update_rapid_variable_current_value",
                new=fake_update,
            ),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/x",
                value="42",
            )

        assert call_order == ["mastership:request", "update", "mastership:release"]

    @pytest.mark.asyncio
    async def test_release_called_even_on_error(
        self, client: MagicMock
    ) -> None:
        released: list[bool] = []

        async def fake_update_fail(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            raise RWSHTTPError("write failed", status_code=403)

        async def fake_release(c: object, *, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        with (
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_release",
                new=fake_release,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.update_rapid_variable_current_value",
                new=fake_update_fail,
            ),
            pytest.raises(RWSHTTPError),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/x",
                value="42",
            )

        assert released == [True]


# ---------------------------------------------------------------------------
# get_variable
# ---------------------------------------------------------------------------


class TestGetVariable:
    @pytest.mark.asyncio
    async def test_returns_parsed_value(self, client: MagicMock) -> None:
        with patch(
            "abb_rws_client.highlevel.rapid.get_rapid_symbol_data",
            new=AsyncMock(
                return_value=_json_resp({"state": [{"value": "123"}]})
            ),
        ):
            result = await get_variable(
                client, symbolurl="RAPID/T_ROB1/MainModule/counter"
            )
        assert result == "123"

    @pytest.mark.asyncio
    async def test_passes_symbolurl(self, client: MagicMock) -> None:
        mock_get = AsyncMock(
            return_value=_json_resp({"state": [{"value": "TRUE"}]})
        )
        with patch(
            "abb_rws_client.highlevel.rapid.get_rapid_symbol_data",
            new=mock_get,
        ):
            await get_variable(client, symbolurl="RAPID/T_ROB1/M/flag")

        mock_get.assert_awaited_once_with(
            client, symbolurl="RAPID/T_ROB1/M/flag"
        )


# ---------------------------------------------------------------------------
# load_module_safe
# ---------------------------------------------------------------------------


class TestLoadModuleSafe:
    @pytest.mark.asyncio
    async def test_unload_then_load_order(self, client: MagicMock) -> None:
        call_order: list[str] = []

        async def fake_mastership(c: object, *, action: str) -> httpx.Response:
            call_order.append(f"mastership:{action}")
            return _resp(status=204)

        async def fake_unload(
            c: object, *, task: str, action: str, module: str
        ) -> httpx.Response:
            call_order.append("unload")
            return _resp(status=204)

        async def fake_load(
            c: object, *, task: str, action: str, modulepath: str
        ) -> httpx.Response:
            call_order.append("load")
            return _resp(status=204)

        with (
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_request",
                new=fake_mastership,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_release",
                new=fake_mastership,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_unload_module_from_rapid_task",
                new=fake_unload,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.load_rapid_module_into_rapid_task",
                new=fake_load,
            ),
        ):
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/my_mod.mod",
                module_name="my_mod",
            )

        assert call_order == [
            "mastership:request",
            "unload",
            "load",
            "mastership:release",
        ]

    @pytest.mark.asyncio
    async def test_unload_error_is_swallowed(self, client: MagicMock) -> None:
        released: list[bool] = []

        async def fake_rel(c: object, *, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        async def fake_unload_fail(
            c: object, *, task: str, action: str, module: str
        ) -> httpx.Response:
            raise RWSHTTPError("not loaded", status_code=404)

        with (
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_release",
                new=fake_rel,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_unload_module_from_rapid_task",
                new=fake_unload_fail,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.load_rapid_module_into_rapid_task",
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
        released: list[bool] = []

        async def fake_rel(c: object, *, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        with (
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_mastership_release",
                new=fake_rel,
            ),
            patch(
                "abb_rws_client.highlevel.rapid.post_unload_module_from_rapid_task",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                "abb_rws_client.highlevel.rapid.load_rapid_module_into_rapid_task",
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


# ---------------------------------------------------------------------------
# Motor control
# ---------------------------------------------------------------------------


class TestMotorControl:
    @pytest.mark.asyncio
    async def test_motors_on(self, client: MagicMock) -> None:
        mock_set = AsyncMock(return_value=_resp(status=204))
        with patch(
            "abb_rws_client.highlevel.rapid.set_controller_state",
            new=mock_set,
        ):
            await set_motors_on(client)

        mock_set.assert_awaited_once_with(
            client, action="setctrlstate", ctrl_state="motoron"
        )

    @pytest.mark.asyncio
    async def test_motors_off(self, client: MagicMock) -> None:
        mock_set = AsyncMock(return_value=_resp(status=204))
        with patch(
            "abb_rws_client.highlevel.rapid.set_controller_state",
            new=mock_set,
        ):
            await set_motors_off(client)

        mock_set.assert_awaited_once_with(
            client, action="setctrlstate", ctrl_state="motoroff"
        )
