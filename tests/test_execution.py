# tests/test_execution.py
"""
Tests unitaires pour execution.py — aucun robot requis.
"""

from __future__ import annotations

import json

import httpx
import pytest

from abb_rws_client.client import RWSClient
from abb_rws_client.exceptions import RWSValueError
from abb_rws_client.execution import (
    _extract_execution_state,
    get_execution_state,
    is_running,
    reset_pp,
    start_execution,
    stop_execution,
)

# ---------------------------------------------------------------------------
# Helpers mock
# ---------------------------------------------------------------------------


def _resp(status_code: int, body: dict | None = None) -> httpx.Response:  # type: ignore[type-arg]
    content = json.dumps(body).encode() if body else b""
    return httpx.Response(status_code=status_code, content=content)


def _exec_response(ctrlexecstate: str, cycle: str = "once", excstate: str = "stopped") -> dict:  # type: ignore[type-arg]
    return {"state": [{"ctrlexecstate": ctrlexecstate, "cycle": cycle, "excstate": excstate}]}


class _RouteTransport(httpx.AsyncBaseTransport):
    def __init__(self, routes: dict[str, httpx.Response]) -> None:  # type: ignore[type-arg]
        self._routes = routes
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


async def _make_client(transport: httpx.AsyncBaseTransport) -> RWSClient:
    client = RWSClient(host="192.168.125.1")
    client._http = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


# ---------------------------------------------------------------------------
# _extract_execution_state
# ---------------------------------------------------------------------------


class TestExtractExecutionState:
    def test_valid_stopped(self) -> None:
        data = _exec_response("stopped", "once", "stopped")
        state = _extract_execution_state(data)
        assert state.ctrlexecstate == "stopped"
        assert state.cycle == "once"
        assert state.excstate == "stopped"

    def test_valid_running(self) -> None:
        state = _extract_execution_state(_exec_response("running"))
        assert state.ctrlexecstate == "running"

    def test_missing_state_key(self) -> None:
        with pytest.raises(RWSValueError):
            _extract_execution_state({})

    def test_empty_state_list(self) -> None:
        with pytest.raises(RWSValueError):
            _extract_execution_state({"state": []})

    def test_missing_ctrlexecstate(self) -> None:
        with pytest.raises(RWSValueError):
            _extract_execution_state({"state": [{"cycle": "once"}]})

    def test_optional_fields_default_empty(self) -> None:
        """cycle et excstate sont optionnels — défaut à chaîne vide."""
        state = _extract_execution_state({"state": [{"ctrlexecstate": "stopped"}]})
        assert state.cycle == ""
        assert state.excstate == ""

    def test_frozen_dataclass(self) -> None:
        state = _extract_execution_state(_exec_response("stopped"))
        with pytest.raises(Exception):
            state.ctrlexecstate = "running"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# get_execution_state
# ---------------------------------------------------------------------------


class TestGetExecutionState:
    async def test_stopped(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution": _resp(200, _exec_response("stopped")),
        })
        client = await _make_client(transport)
        state = await get_execution_state(client)
        assert state.ctrlexecstate == "stopped"

    async def test_running(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution": _resp(200, _exec_response("running")),
        })
        client = await _make_client(transport)
        state = await get_execution_state(client)
        assert state.ctrlexecstate == "running"

    async def test_json_param_sent(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution": _resp(200, _exec_response("stopped")),
        })
        client = await _make_client(transport)
        await get_execution_state(client)
        assert "json=1" in str(transport.requests[0].url)

    async def test_invalid_json_raises(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution": httpx.Response(200, content=b"not json"),
        })
        client = await _make_client(transport)
        with pytest.raises(RWSValueError, match="JSON"):
            await get_execution_state(client)


# ---------------------------------------------------------------------------
# is_running
# ---------------------------------------------------------------------------


class TestIsRunning:
    async def test_true_when_running(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution": _resp(200, _exec_response("running")),
        })
        client = await _make_client(transport)
        assert await is_running(client) is True

    async def test_false_when_stopped(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution": _resp(200, _exec_response("stopped")),
        })
        client = await _make_client(transport)
        assert await is_running(client) is False


# ---------------------------------------------------------------------------
# start_execution
# ---------------------------------------------------------------------------


class TestStartExecution:
    async def test_default_payload(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/start": _resp(204),
        })
        client = await _make_client(transport)
        await start_execution(client)
        req = transport.requests[0]
        assert req.method == "POST"
        body = req.content.decode()
        assert "regain=continue" in body
        assert "execmode=continue" in body
        assert "cycle=once" in body
        assert "stopatbp=disabled" in body

    async def test_mastership_implicit_param(self) -> None:
        """start_execution doit envoyer ?mastership=implicit en query string."""
        transport = _RouteTransport({
            "rw/rapid/execution/start": _resp(204),
        })
        client = await _make_client(transport)
        await start_execution(client)
        assert "mastership=implicit" in str(transport.requests[0].url)

    async def test_custom_cycle(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/start": _resp(204),
        })
        client = await _make_client(transport)
        await start_execution(client, cycle="forever")
        assert b"cycle=forever" in transport.requests[0].content

    async def test_stopatbp_enabled(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/start": _resp(204),
        })
        client = await _make_client(transport)
        await start_execution(client, stopatbp=True)
        assert b"stopatbp=enabled" in transport.requests[0].content


# ---------------------------------------------------------------------------
# stop_execution
# ---------------------------------------------------------------------------


class TestStopExecution:
    async def test_default_stopmode(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/stop": _resp(204),
        })
        client = await _make_client(transport)
        await stop_execution(client)
        req = transport.requests[0]
        assert req.method == "POST"
        assert b"stopmode=stop" in req.content

    async def test_quick_stop(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/stop": _resp(204),
        })
        client = await _make_client(transport)
        await stop_execution(client, stopmode="quick_stop")
        assert b"stopmode=quick_stop" in transport.requests[0].content


# ---------------------------------------------------------------------------
# reset_pp
# ---------------------------------------------------------------------------


class TestResetPP:
    async def test_post_to_correct_path(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/resetpp": _resp(204),
        })
        client = await _make_client(transport)
        await reset_pp(client)
        req = transport.requests[0]
        assert req.method == "POST"
        assert "resetpp" in req.url.path

    async def test_returns_none(self) -> None:
        transport = _RouteTransport({
            "rw/rapid/execution/resetpp": _resp(204),
        })
        client = await _make_client(transport)
        result = await reset_pp(client)
        assert result is None
