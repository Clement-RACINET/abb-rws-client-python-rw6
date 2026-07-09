# tests/test_rws_execution.py
"""
Tests unitaires pour rws/rapid/execution.py — aucun robot requis.

Couverture :
    - get_execution_state  : succès (200), paramètre json=1, erreur 401
    - start_execution      : succès (204), paramètres par défaut, paramètres custom, 409
    - stop_execution       : succès (204), paramètre stopmode, 409
    - reset_program_pointer: succès (204), route correcte, 409
"""

from __future__ import annotations

import httpx
import pytest

from abb_rws_client._core.client import RWSClient
from abb_rws_client._core.exceptions import RWSAuthenticationError, RWSHTTPError
from abb_rws_client.rws.rapid.execution import (
    get_execution_state,
    reset_program_pointer,
    start_execution,
    stop_execution,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resp(status_code: int, content: bytes = b"{}") -> httpx.Response:
    return httpx.Response(status_code=status_code, content=content)


class _FixedTransport(httpx.AsyncBaseTransport):
    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._response


def _inject(client: RWSClient, transport: httpx.AsyncBaseTransport) -> RWSClient:
    client._http = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


# ---------------------------------------------------------------------------
# get_execution_state
# ---------------------------------------------------------------------------

class TestGetExecutionState:
    async def test_returns_200(self) -> None:
        transport = _FixedTransport(_resp(200, b'{"ctrlexecstate": "stopped"}'))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        resp = await get_execution_state(client)
        assert resp.status_code == 200

    async def test_calls_correct_route(self) -> None:
        transport = _FixedTransport(_resp(200))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await get_execution_state(client)
        assert transport.requests[0].url.path == "/rw/rapid/execution"

    async def test_uses_get_method(self) -> None:
        transport = _FixedTransport(_resp(200))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await get_execution_state(client)
        assert transport.requests[0].method == "GET"

    async def test_sends_json_param(self) -> None:
        transport = _FixedTransport(_resp(200))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await get_execution_state(client)
        assert "json=1" in str(transport.requests[0].url)

    async def test_401_raises_auth_error(self) -> None:
        transport = _FixedTransport(_resp(401))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSAuthenticationError):
            await get_execution_state(client)


# ---------------------------------------------------------------------------
# start_execution
# ---------------------------------------------------------------------------

class TestStartExecution:
    async def test_returns_204_on_success(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        resp = await start_execution(client)
        assert resp.status_code == 204

    async def test_calls_correct_route(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await start_execution(client)
        assert transport.requests[0].url.path == "/rw/rapid/execution/start"

    async def test_uses_post_method(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await start_execution(client)
        assert transport.requests[0].method == "POST"

    async def test_default_params_sent(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await start_execution(client)
        body = transport.requests[0].content.decode()
        assert "regain=continue" in body
        assert "execmode=continue" in body
        assert "cycle=forever" in body

    async def test_custom_cycle_param(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await start_execution(client, cycle="once")
        body = transport.requests[0].content.decode()
        assert "cycle=once" in body

    async def test_409_raises_http_error(self) -> None:
        transport = _FixedTransport(_resp(409, b"Already running"))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await start_execution(client)
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# stop_execution
# ---------------------------------------------------------------------------

class TestStopExecution:
    async def test_returns_204_on_success(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        resp = await stop_execution(client)
        assert resp.status_code == 204

    async def test_calls_correct_route(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await stop_execution(client)
        assert transport.requests[0].url.path == "/rw/rapid/execution/stop"

    async def test_default_stopmode_sent(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await stop_execution(client)
        body = transport.requests[0].content.decode()
        assert "stopmode=cycle" in body

    async def test_custom_stopmode(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await stop_execution(client, stopmode="instr")
        body = transport.requests[0].content.decode()
        assert "stopmode=instr" in body

    async def test_409_raises_http_error(self) -> None:
        transport = _FixedTransport(_resp(409, b"Already stopped"))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await stop_execution(client)
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# reset_program_pointer
# ---------------------------------------------------------------------------

class TestResetProgramPointer:
    async def test_returns_204_on_success(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        resp = await reset_program_pointer(client)
        assert resp.status_code == 204

    async def test_calls_correct_route(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await reset_program_pointer(client)
        assert transport.requests[0].url.path == "/rw/rapid/execution/resetpp"

    async def test_uses_post_method(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await reset_program_pointer(client)
        assert transport.requests[0].method == "POST"

    async def test_409_raises_http_error(self) -> None:
        transport = _FixedTransport(_resp(409, b"Running"))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await reset_program_pointer(client)
        assert exc_info.value.status_code == 409
