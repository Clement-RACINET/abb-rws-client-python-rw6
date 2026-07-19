# tests/highlevel/test_rapid.py
"""Tests for abb_rws_client_python_rw6.highlevel.rapid.

Covers all public functions and internal helpers.
All rws/ dependencies are mocked via unittest.mock.AsyncMock — no HTTP
calls are made.

Mock targets are the names as imported in ``highlevel.rapid``, not the
original module paths.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from abb_rws_client_python_rw6.core.exceptions import RWSHTTPError
from abb_rws_client_python_rw6.highlevel.rapid import (
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

_MODULE = "abb_rws_client_python_rw6.highlevel.rapid"


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


# ---------------------------------------------------------------------------
# _parse_exec_state
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# _parse_symbol_value
# ---------------------------------------------------------------------------


class TestParseSymbolValue:
    """Unit tests for the _parse_symbol_value helper."""

    def test_json_value(self) -> None:
        assert _parse_symbol_value(_json_resp({"state": [{"value": "42"}]})) == "42"

    def test_xml_value(self) -> None:
        assert _parse_symbol_value(_resp('<span class="value">TRUE</span>')) == "TRUE"

    def test_raises_on_unparseable(self) -> None:
        with pytest.raises(ValueError, match="symbol value"):
            _parse_symbol_value(_resp("<html></html>"))

    def test_json_value_numeric_cast(self) -> None:
        """Numeric values stored as int in JSON must be cast to str."""
        assert _parse_symbol_value(_json_resp({"state": [{"value": 99}]})) == "99"


# ---------------------------------------------------------------------------
# is_running
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# start_rapid
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# stop_rapid
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# wait_until_stopped
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# set_variable_with_mastership
# ---------------------------------------------------------------------------
# rapid.py utilise post_mastership_domain_request / post_mastership_domain_release
# (POST /rw/mastership/{domain}) — signatures : (client, *, domain, action).


class TestSetVariableWithMastership:
    """Tests for set_variable_with_mastership()."""

    @pytest.mark.asyncio
    async def test_request_write_release_order(self, client: MagicMock) -> None:
        call_order: list[str] = []

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:request")
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:release")
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
                f"{_MODULE}.post_mastership_domain_request",
                new=fake_request,
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=fake_release,
            ),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
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
    async def test_release_called_even_on_error(self, client: MagicMock) -> None:
        """Mastership must be released even when the write raises."""
        released: list[bool] = []

        async def fake_update_fail(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            raise RWSHTTPError("write failed", status_code=403)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=fake_release,
            ),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
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

    @pytest.mark.asyncio
    async def test_update_called_with_correct_args(self, client: MagicMock) -> None:
        """update_rapid_variable_current_value must receive action='set'."""
        mock_update = AsyncMock(return_value=_resp(status=204))
        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=mock_update,
            ),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/M/counter",
                value="99",
            )

        mock_update.assert_awaited_once_with(
            client,
            symbolurl="RAPID/T_ROB1/M/counter",
            action="set",
            value="99",
        )

    @pytest.mark.asyncio
    async def test_default_domain_is_rapid(self, client: MagicMock) -> None:
        """Default domain must be 'rapid'."""
        captured: dict[str, str] = {}

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            captured["domain"] = domain
            return _resp(status=204)

        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=fake_request,
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/M/x",
                value="1",
            )

        assert captured["domain"] == "rapid"


# ---------------------------------------------------------------------------
# get_variable
# ---------------------------------------------------------------------------


class TestGetVariable:
    """Tests for get_variable()."""

    @pytest.mark.asyncio
    async def test_returns_parsed_value(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.get_rapid_symbol_data",
            new=AsyncMock(return_value=_json_resp({"state": [{"value": "123"}]})),
        ):
            result = await get_variable(client, symbolurl="RAPID/T_ROB1/MainModule/counter")
        assert result == "123"

    @pytest.mark.asyncio
    async def test_passes_symbolurl(self, client: MagicMock) -> None:
        mock_get = AsyncMock(return_value=_json_resp({"state": [{"value": "TRUE"}]}))
        with patch(f"{_MODULE}.get_rapid_symbol_data", new=mock_get):
            await get_variable(client, symbolurl="RAPID/T_ROB1/M/flag")

        mock_get.assert_awaited_once_with(client, symbolurl="RAPID/T_ROB1/M/flag")

    @pytest.mark.asyncio
    async def test_returns_xml_value(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.get_rapid_symbol_data",
            new=AsyncMock(return_value=_resp('<span class="value">3.14</span>')),
        ):
            result = await get_variable(client, symbolurl="RAPID/T_ROB1/M/pi")
        assert result == "3.14"


# ---------------------------------------------------------------------------
# load_module_safe
# ---------------------------------------------------------------------------
# rapid.py utilise post_mastership_domain_request / post_mastership_domain_release
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
            patch(
                f"{_MODULE}.reset_rapid_program_pointer_to_main",
                new=fake_reset,
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=fake_request,
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=fake_release,
            ),
            patch(
                f"{_MODULE}.post_unload_module_from_rapid_task",
                new=fake_unload,
            ),
            patch(
                f"{_MODULE}.load_rapid_module_into_rapid_task",
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
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=fake_release,
            ),
            patch(
                f"{_MODULE}.post_unload_module_from_rapid_task",
                new=fake_unload_fail,
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
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=fake_release,
            ),
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
            patch(
                f"{_MODULE}.reset_rapid_program_pointer_to_main",
                new=fake_reset_fail,
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=fake_request,
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=fake_release,
            ),
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
            patch(
                f"{_MODULE}.load_rapid_module_into_rapid_task",
                new=mock_load,
            ),
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


# ---------------------------------------------------------------------------
# Motor control
# ---------------------------------------------------------------------------


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
