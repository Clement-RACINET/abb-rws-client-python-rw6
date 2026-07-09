# tests/test_client.py
"""
Tests unitaires pour RWSClient (async) et RWSClientSync.

Couverture ciblée :
- Cycle de vie : aopen / aclose / context manager / idempotence
- Méthodes HTTP : get / put / post / delete
- Politique de retry : déclencheurs, comptage, délai, jitter
- Validation status codes : 200, 204, 401, 404, 4xx, 5xx
- Erreurs transport → exceptions RWS custom
- __repr__ (open + closed)
- RWSClientSync : même couverture en synchrone
- Helpers : _build_auth, _retry_delay, _raise_for_status
"""

from __future__ import annotations

import httpx
import pytest

from abb_rws_client._core.client import (
    _RETRY_BASE_DELAY,
    _RETRY_JITTER,
    _RETRY_MAX_ATTEMPTS,
    _build_auth,
    _raise_for_status,
    _retry_delay,
    RWSClient,
    RWSClientSync,
)
from abb_rws_client._core.exceptions import (
    RWSAuthenticationError,
    RWSConnectionError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
)


# ---------------------------------------------------------------------------
# Helpers de mock — async
# ---------------------------------------------------------------------------


def _resp(status_code: int, content: bytes = b"{}") -> httpx.Response:
    """Crée une réponse httpx minimale."""
    return httpx.Response(status_code=status_code, content=content)


class _SequentialTransport(httpx.AsyncBaseTransport):
    """Retourne les réponses dans l'ordre de la liste fournie."""

    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._index >= len(self._responses):
            return _resp(200)
        item = self._responses[self._index]
        self._index += 1
        if isinstance(item, Exception):
            raise item
        return item


class _RouteTransport(httpx.AsyncBaseTransport):
    """Retourne une réponse fixe par chemin URL."""

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        self._routes = routes
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


# ---------------------------------------------------------------------------
# Helpers de mock — sync
# ---------------------------------------------------------------------------


class _SequentialSyncTransport(httpx.BaseTransport):
    """Version synchrone de _SequentialTransport."""

    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._index >= len(self._responses):
            return _resp(200)
        item = self._responses[self._index]
        self._index += 1
        if isinstance(item, Exception):
            raise item
        return item


class _RouteSyncTransport(httpx.BaseTransport):
    """Version synchrone de _RouteTransport."""

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        self._routes = routes
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


# ---------------------------------------------------------------------------
# Helpers d'injection
# ---------------------------------------------------------------------------


def _inject(client: RWSClient, transport: httpx.AsyncBaseTransport) -> RWSClient:
    """Injecte un transport mocké dans un RWSClient déjà ouvert."""
    client._http = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


def _inject_sync(client: RWSClientSync, transport: httpx.BaseTransport) -> RWSClientSync:
    """Injecte un transport mocké dans un RWSClientSync déjà ouvert."""
    client._http = httpx.Client(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


async def _open_client(
    transport: httpx.AsyncBaseTransport,
    **kwargs: object,
) -> RWSClient:
    """Crée et ouvre un RWSClient avec transport mocké."""
    client = RWSClient(host="192.168.125.1", **kwargs)  # type: ignore[arg-type]
    _inject(client, transport)
    return client


def _open_sync_client(
    transport: httpx.BaseTransport,
    **kwargs: object,
) -> RWSClientSync:
    """Crée et ouvre un RWSClientSync avec transport mocké."""
    client = RWSClientSync(host="192.168.125.1", **kwargs)  # type: ignore[arg-type]
    _inject_sync(client, transport)
    return client


# ===========================================================================
# Tests des helpers purs
# ===========================================================================


class TestBuildAuth:
    def test_returns_digest_auth(self) -> None:
        auth = _build_auth("Default User", "robotics")
        assert isinstance(auth, httpx.DigestAuth)

    def test_custom_credentials(self) -> None:
        auth = _build_auth("admin", "secret")
        assert isinstance(auth, httpx.DigestAuth)


class TestRetryDelay:
    def test_attempt_0_is_near_base(self) -> None:
        """Attempt 0 → délai proche de _RETRY_BASE_DELAY * 1."""
        delay = _retry_delay(0)
        base = _RETRY_BASE_DELAY * (2**0)
        assert base * (1 - _RETRY_JITTER) <= delay <= base * (1 + _RETRY_JITTER)

    def test_attempt_1_is_near_double(self) -> None:
        """Attempt 1 → délai proche de _RETRY_BASE_DELAY * 2."""
        delay = _retry_delay(1)
        base = _RETRY_BASE_DELAY * (2**1)
        assert base * (1 - _RETRY_JITTER) <= delay <= base * (1 + _RETRY_JITTER)

    def test_returns_float(self) -> None:
        assert isinstance(_retry_delay(0), float)


class TestRaiseForStatus:
    def test_200_does_not_raise(self) -> None:
        _raise_for_status(_resp(200), "rw/test")  # pas d'exception

    def test_204_does_not_raise(self) -> None:
        _raise_for_status(_resp(204), "rw/test")

    def test_401_raises_auth_error(self) -> None:
        with pytest.raises(RWSAuthenticationError):
            _raise_for_status(_resp(401), "rw/test")

    def test_404_raises_not_found_with_path(self) -> None:
        with pytest.raises(RWSNotFoundError) as exc_info:
            _raise_for_status(_resp(404), "rw/rapid/symbol")
        assert "rw/rapid/symbol" in exc_info.value.resource

    def test_403_raises_http_error(self) -> None:
        with pytest.raises(RWSHTTPError) as exc_info:
            _raise_for_status(_resp(403), "rw/test")
        assert exc_info.value.status_code == 403

    def test_500_raises_http_error(self) -> None:
        with pytest.raises(RWSHTTPError) as exc_info:
            _raise_for_status(_resp(500), "rw/test")
        assert exc_info.value.status_code == 500

    def test_400_raises_http_error(self) -> None:
        with pytest.raises(RWSHTTPError) as exc_info:
            _raise_for_status(_resp(400), "rw/test")
        assert exc_info.value.status_code == 400


# ===========================================================================
# RWSClient — async
# ===========================================================================


class TestClientLifecycle:
    async def test_context_manager_opens_and_closes(self) -> None:
        async with RWSClient(host="192.168.125.1") as client:
            assert client._http is not None
        assert client._http is None

    async def test_aopen_idempotent(self) -> None:
        client = RWSClient(host="192.168.125.1")
        await client.aopen()
        http_first = client._http
        await client.aopen()
        assert client._http is http_first
        await client.aclose()

    async def test_aclose_idempotent(self) -> None:
        client = RWSClient(host="192.168.125.1")
        await client.aopen()
        await client.aclose()
        await client.aclose()
        assert client._http is None

    async def test_request_before_open_raises_runtime_error(self) -> None:
        client = RWSClient(host="192.168.125.1")
        with pytest.raises(RuntimeError, match="not open"):
            await client.get("rw/rapid/execution")

    async def test_repr_open(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        r = repr(client)
        assert "open" in r
        assert "192.168.125.1" in r

    async def test_repr_closed(self) -> None:
        client = RWSClient(host="192.168.125.1")
        r = repr(client)
        assert "closed" in r
        assert "192.168.125.1" in r

    async def test_custom_port_in_base_url(self) -> None:
        client = RWSClient(host="10.0.0.1", port=8080)
        assert "8080" in client.base_url

    async def test_custom_credentials_stored(self) -> None:
        client = RWSClient(host="10.0.0.1", username="admin", password="secret")
        assert client.username == "admin"
        assert client.password == "secret"


class TestHttpMethods:
    async def test_get_returns_response(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(200, b'{"ok": true}')})
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200

    async def test_get_sends_query_params(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        await client.get("rw/test", params={"json": "1"})
        sent = transport.requests[0]
        assert "json=1" in str(sent.url)

    async def test_put_sends_form_data(self) -> None:
        transport = _RouteTransport(
            {"rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR": _resp(204)}
        )
        client = await _open_client(transport)
        await client.put(
            "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            data={"value": "42"},
        )
        sent = transport.requests[0]
        assert sent.method == "PUT"
        assert b"value=42" in sent.content

    async def test_post_sends_correct_method(self) -> None:
        transport = _RouteTransport({"rw/mastership/request": _resp(204)})
        client = await _open_client(transport)
        await client.post("rw/mastership/request")
        assert transport.requests[0].method == "POST"

    async def test_delete_sends_correct_method(self) -> None:
        transport = _RouteTransport({"rw/rapid/tasks/T_ROB1": _resp(204)})
        client = await _open_client(transport)
        await client.delete("rw/rapid/tasks/T_ROB1")
        assert transport.requests[0].method == "DELETE"

    async def test_204_is_valid_response(self) -> None:
        transport = _RouteTransport({"rw/mastership/release": _resp(204)})
        client = await _open_client(transport)
        response = await client.post("rw/mastership/release")
        assert response.status_code == 204


class TestStatusCodeValidation:
    async def test_401_raises_auth_error(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(401)})
        client = await _open_client(transport)
        with pytest.raises(RWSAuthenticationError):
            await client.get("rw/test")

    async def test_404_raises_not_found(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(404)})
        client = await _open_client(transport)
        with pytest.raises(RWSNotFoundError) as exc_info:
            await client.get("rw/test")
        assert "rw/test" in exc_info.value.resource

    async def test_403_raises_http_error(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(403)})
        client = await _open_client(transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await client.get("rw/test")
        assert exc_info.value.status_code == 403

    async def test_500_raises_http_error(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(500)})
        client = await _open_client(transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await client.get("rw/test")
        assert exc_info.value.status_code == 500

    async def test_200_returns_response(self) -> None:
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200


class TestRetryPolicy:
    async def test_retry_on_connect_error(self) -> None:
        """ConnectError déclenche un retry — succès au 2e essai."""
        transport = _SequentialTransport([
            httpx.ConnectError("connection refused"),
            _resp(200),
        ])
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2

    async def test_retry_on_read_timeout(self) -> None:
        """ReadTimeout déclenche un retry — succès au 2e essai."""
        transport = _SequentialTransport([
            httpx.ReadTimeout("read timeout"),
            _resp(200),
        ])
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200

    async def test_retry_on_pool_timeout(self) -> None:
        """PoolTimeout déclenche un retry — succès au 2e essai."""
        transport = _SequentialTransport([
            httpx.PoolTimeout("pool timeout"),
            _resp(200),
        ])
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200

    async def test_retry_exhausted_connect_error_raises_connection_error(self) -> None:
        """Après épuisement des retries sur ConnectError → RWSConnectionError."""
        transport = _SequentialTransport(
            [httpx.ConnectError("refused")] * _RETRY_MAX_ATTEMPTS
        )
        client = await _open_client(transport)
        with pytest.raises(RWSConnectionError):
            await client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS

    async def test_retry_exhausted_read_timeout_raises_timeout_error(self) -> None:
        """Après épuisement des retries sur ReadTimeout → RWSTimeoutError."""
        transport = _SequentialTransport(
            [httpx.ReadTimeout("timeout")] * _RETRY_MAX_ATTEMPTS
        )
        client = await _open_client(transport)
        with pytest.raises(RWSTimeoutError):
            await client.get("rw/test")

    async def test_retry_exhausted_pool_timeout_raises_timeout_error(self) -> None:
        """Après épuisement des retries sur PoolTimeout → RWSTimeoutError."""
        transport = _SequentialTransport(
            [httpx.PoolTimeout("pool")] * _RETRY_MAX_ATTEMPTS
        )
        client = await _open_client(transport)
        with pytest.raises(RWSTimeoutError):
            await client.get("rw/test")

    async def test_http_error_not_retried(self) -> None:
        """Une erreur HTTP 500 n'est pas retentée — 1 seule requête."""
        transport = _SequentialTransport([_resp(500), _resp(200)])
        client = await _open_client(transport)
        with pytest.raises(RWSHTTPError):
            await client.get("rw/test")
        assert len(transport.requests) == 1

    async def test_exact_retry_count(self) -> None:
        """Vérifie que le nombre de tentatives est exactement _RETRY_MAX_ATTEMPTS."""
        transport = _SequentialTransport(
            [httpx.ConnectError("refused")] * _RETRY_MAX_ATTEMPTS
        )
        client = await _open_client(transport)
        with pytest.raises(RWSConnectionError):
            await client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS


# ===========================================================================
# RWSClientSync
# ===========================================================================


class TestRWSClientSyncLifecycle:
    def test_context_manager_opens_and_closes(self) -> None:
        with RWSClientSync(host="192.168.125.1") as client:
            assert client._http is not None
        assert client._http is None

    def test_open_idempotent(self) -> None:
        client = RWSClientSync(host="192.168.125.1")
        client.open()
        http_first = client._http
        client.open()
        assert client._http is http_first
        client.close()

    def test_close_idempotent(self) -> None:
        client = RWSClientSync(host="192.168.125.1")
        client.open()
        client.close()
        client.close()
        assert client._http is None

    def test_request_before_open_raises_runtime_error(self) -> None:
        client = RWSClientSync(host="192.168.125.1")
        with pytest.raises(RuntimeError, match="not open"):
            client.get("rw/rapid/execution")

    def test_repr_open(self) -> None:
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        r = repr(client)
        assert "open" in r
        assert "192.168.125.1" in r

    def test_repr_closed(self) -> None:
        client = RWSClientSync(host="192.168.125.1")
        r = repr(client)
        assert "closed" in r


class TestRWSClientSyncHttpMethods:
    def test_get_returns_response(self) -> None:
        transport = _RouteSyncTransport({"rw/test": _resp(200, b'{"ok": true}')})
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200

    def test_get_sends_query_params(self) -> None:
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        client.get("rw/test", params={"json": "1"})
        sent = transport.requests[0]
        assert "json=1" in str(sent.url)

    def test_put_sends_form_data(self) -> None:
        transport = _RouteSyncTransport(
            {"rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR": _resp(204)}
        )
        client = _open_sync_client(transport)
        client.put(
            "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            data={"value": "42"},
        )
        sent = transport.requests[0]
        assert sent.method == "PUT"
        assert b"value=42" in sent.content

    def test_post_sends_correct_method(self) -> None:
        transport = _RouteSyncTransport({"rw/mastership/request": _resp(204)})
        client = _open_sync_client(transport)
        client.post("rw/mastership/request")
        assert transport.requests[0].method == "POST"

    def test_delete_sends_correct_method(self) -> None:
        transport = _RouteSyncTransport({"rw/rapid/tasks/T_ROB1": _resp(204)})
        client = _open_sync_client(transport)
        client.delete("rw/rapid/tasks/T_ROB1")
        assert transport.requests[0].method == "DELETE"

    def test_204_is_valid_response(self) -> None:
        transport = _RouteSyncTransport({"rw/mastership/release": _resp(204)})
        client = _open_sync_client(transport)
        response = client.post("rw/mastership/release")
        assert response.status_code == 204


class TestRWSClientSyncStatusCodes:
    def test_401_raises_auth_error(self) -> None:
        transport = _RouteSyncTransport({"rw/test": _resp(401)})
        client = _open_sync_client(transport)
        with pytest.raises(RWSAuthenticationError):
            client.get("rw/test")

    def test_404_raises_not_found(self) -> None:
        transport = _RouteSyncTransport({"rw/test": _resp(404)})
        client = _open_sync_client(transport)
        with pytest.raises(RWSNotFoundError) as exc_info:
            client.get("rw/test")
        assert "rw/test" in exc_info.value.resource

    def test_500_raises_http_error(self) -> None:
        transport = _RouteSyncTransport({"rw/test": _resp(500)})
        client = _open_sync_client(transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            client.get("rw/test")
        assert exc_info.value.status_code == 500


class TestRWSClientSyncRetryPolicy:
    def test_retry_on_connect_error(self) -> None:
        transport = _SequentialSyncTransport([
            httpx.ConnectError("refused"),
            _resp(200),
        ])
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2

    def test_retry_on_read_timeout(self) -> None:
        transport = _SequentialSyncTransport([
            httpx.ReadTimeout("timeout"),
            _resp(200),
        ])
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200

    def test_retry_on_pool_timeout(self) -> None:
        transport = _SequentialSyncTransport([
            httpx.PoolTimeout("pool"),
            _resp(200),
        ])
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200

    def test_retry_exhausted_connect_error_raises_connection_error(self) -> None:
        transport = _SequentialSyncTransport(
            [httpx.ConnectError("refused")] * _RETRY_MAX_ATTEMPTS
        )
        client = _open_sync_client(transport)
        with pytest.raises(RWSConnectionError):
            client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS

    def test_retry_exhausted_timeout_raises_timeout_error(self) -> None:
        transport = _SequentialSyncTransport(
            [httpx.ReadTimeout("timeout")] * _RETRY_MAX_ATTEMPTS
        )
        client = _open_sync_client(transport)
        with pytest.raises(RWSTimeoutError):
            client.get("rw/test")

    def test_http_error_not_retried(self) -> None:
        transport = _SequentialSyncTransport([_resp(500), _resp(200)])
        client = _open_sync_client(transport)
        with pytest.raises(RWSHTTPError):
            client.get("rw/test")
        assert len(transport.requests) == 1
