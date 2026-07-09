# tests/test_rws_mastership.py
"""
Tests unitaires pour rws/mastership.py — aucun robot requis.

Couverture :
    - mastership_request : succès (204), erreur 409, erreur 401
    - mastership_release : succès (204), erreur 409, erreur 401
    - Vérification de la route et de la méthode HTTP
"""

from __future__ import annotations

import httpx
import pytest

from abb_rws_client._core.client import RWSClient
from abb_rws_client._core.exceptions import RWSAuthenticationError, RWSHTTPError
from abb_rws_client.rws.mastership import mastership_release, mastership_request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resp(status_code: int, content: bytes = b"") -> httpx.Response:
    return httpx.Response(status_code=status_code, content=content)


class _FixedTransport(httpx.AsyncBaseTransport):
    """Retourne toujours la même réponse et enregistre les requêtes."""

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
# mastership_request
# ---------------------------------------------------------------------------

class TestMastershipRequest:
    async def test_returns_204_on_success(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        resp = await mastership_request(client)
        assert resp.status_code == 204

    async def test_calls_correct_route(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await mastership_request(client)
        assert len(transport.requests) == 1
        assert transport.requests[0].url.path == "/rw/mastership/request"

    async def test_uses_post_method(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await mastership_request(client)
        assert transport.requests[0].method == "POST"

    async def test_409_raises_http_error(self) -> None:
        transport = _FixedTransport(_resp(409, b"Conflict"))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await mastership_request(client)
        assert exc_info.value.status_code == 409

    async def test_401_raises_auth_error(self) -> None:
        transport = _FixedTransport(_resp(401))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSAuthenticationError):
            await mastership_request(client)


# ---------------------------------------------------------------------------
# mastership_release
# ---------------------------------------------------------------------------

class TestMastershipRelease:
    async def test_returns_204_on_success(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        resp = await mastership_release(client)
        assert resp.status_code == 204

    async def test_calls_correct_route(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await mastership_release(client)
        assert len(transport.requests) == 1
        assert transport.requests[0].url.path == "/rw/mastership/release"

    async def test_uses_post_method(self) -> None:
        transport = _FixedTransport(_resp(204))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        await mastership_release(client)
        assert transport.requests[0].method == "POST"

    async def test_409_raises_http_error(self) -> None:
        transport = _FixedTransport(_resp(409, b"Not held"))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await mastership_release(client)
        assert exc_info.value.status_code == 409

    async def test_401_raises_auth_error(self) -> None:
        transport = _FixedTransport(_resp(401))
        client = RWSClient(host="192.168.125.1")
        _inject(client, transport)
        with pytest.raises(RWSAuthenticationError):
            await mastership_release(client)
