# tests/test_client.py
"""
Unit tests for RWSClient (async) and RWSClientSync.

Author: Clement RACINET

Coverage:
- Lifecycle: aopen / aclose / context manager / idempotence
- HTTP methods: get / put / post / delete
- Retry policy: triggers, attempt count, delay, jitter
- Status code validation: 200, 204, 401, 404, 4xx, 5xx
- Transport errors → custom RWS exceptions
- __repr__ (open + closed)
- RWSClientSync: same coverage in synchronous mode
- Helpers: _build_auth, _retry_delay, _raise_for_status
"""

from __future__ import annotations

import httpx
import pytest

from abb_rws_client._core.client import (
    _RETRY_BASE_DELAY,
    _RETRY_JITTER,
    _RETRY_MAX_ATTEMPTS,
    RWSClient,
    RWSClientSync,
    _build_auth,
    _raise_for_status,
    _retry_delay,
)
from abb_rws_client._core.exceptions import (
    RWSAuthenticationError,
    RWSConnectionError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
)

# ---------------------------------------------------------------------------
# Mock helpers — async
# ---------------------------------------------------------------------------


def _resp(status_code: int, content: bytes = b"{}") -> httpx.Response:
    """Build a minimal httpx response for testing.

    Args:
        status_code: HTTP status code to set on the response.
        content: Raw response body (default: ``b"{}"``).

    Returns:
        A minimal ``httpx.Response`` instance.
    """
    return httpx.Response(status_code=status_code, content=content)


class _SequentialTransport(httpx.AsyncBaseTransport):
    """Async transport that returns responses in the order of the provided list.

    Args:
        responses: Ordered list of responses or exceptions to return.
            Once the list is exhausted, every subsequent request returns HTTP 200.

    Attributes:
        requests: List of all ``httpx.Request`` objects received.
    """

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
    """Async transport that returns a fixed response per URL path.

    Args:
        routes: Mapping of URL path (without leading ``/``) to response.
            Unmatched paths return HTTP 404.

    Attributes:
        requests: List of all ``httpx.Request`` objects received.
    """

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        self._routes = routes
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


# ---------------------------------------------------------------------------
# Mock helpers — sync
# ---------------------------------------------------------------------------


class _SequentialSyncTransport(httpx.BaseTransport):
    """Synchronous counterpart of ``_SequentialTransport``.

    Args:
        responses: Ordered list of responses or exceptions to return.

    Attributes:
        requests: List of all ``httpx.Request`` objects received.
    """

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
    """Synchronous counterpart of ``_RouteTransport``.

    Args:
        routes: Mapping of URL path (without leading ``/``) to response.

    Attributes:
        requests: List of all ``httpx.Request`` objects received.
    """

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        self._routes = routes
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


# ---------------------------------------------------------------------------
# Injection helpers
# ---------------------------------------------------------------------------


def _inject(client: RWSClient, transport: httpx.AsyncBaseTransport) -> RWSClient:
    """Inject a mock transport into an already-instantiated RWSClient.

    Bypasses the real HTTP layer by replacing ``client._http`` with a
    fresh ``httpx.AsyncClient`` backed by the provided transport.

    Args:
        client: Target ``RWSClient`` instance (need not be open).
        transport: Mock async transport to inject.

    Returns:
        The same ``client`` instance with the transport injected.
    """
    client._http = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


def _inject_sync(client: RWSClientSync, transport: httpx.BaseTransport) -> RWSClientSync:
    """Inject a mock transport into an already-instantiated RWSClientSync.

    Args:
        client: Target ``RWSClientSync`` instance (need not be open).
        transport: Mock sync transport to inject.

    Returns:
        The same ``client`` instance with the transport injected.
    """
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
    """Create and open an RWSClient with a mock transport.

    Args:
        transport: Mock async transport to inject.
        **kwargs: Additional keyword arguments forwarded to ``RWSClient``.

    Returns:
        An ``RWSClient`` instance with the mock transport ready to use.
    """
    client = RWSClient(host="192.168.125.1", **kwargs)  # type: ignore[arg-type]
    _inject(client, transport)
    return client


def _open_sync_client(
    transport: httpx.BaseTransport,
    **kwargs: object,
) -> RWSClientSync:
    """Create and open an RWSClientSync with a mock transport.

    Args:
        transport: Mock sync transport to inject.
        **kwargs: Additional keyword arguments forwarded to ``RWSClientSync``.

    Returns:
        An ``RWSClientSync`` instance with the mock transport ready to use.
    """
    client = RWSClientSync(host="192.168.125.1", **kwargs)  # type: ignore[arg-type]
    _inject_sync(client, transport)
    return client


# ===========================================================================
# Pure helper tests
# ===========================================================================


class TestBuildAuth:
    def test_returns_digest_auth(self) -> None:
        """_build_auth returns an httpx.DigestAuth instance."""
        auth = _build_auth("Default User", "robotics")
        assert isinstance(auth, httpx.DigestAuth)

    def test_custom_credentials(self) -> None:
        """_build_auth accepts arbitrary username/password pairs."""
        auth = _build_auth("admin", "secret")
        assert isinstance(auth, httpx.DigestAuth)


class TestRetryDelay:
    def test_attempt_0_is_near_base(self) -> None:
        """Attempt 0 → delay close to _RETRY_BASE_DELAY * 1."""
        delay = _retry_delay(0)
        base = _RETRY_BASE_DELAY * (2**0)
        assert base * (1 - _RETRY_JITTER) <= delay <= base * (1 + _RETRY_JITTER)

    def test_attempt_1_is_near_double(self) -> None:
        """Attempt 1 → delay close to _RETRY_BASE_DELAY * 2."""
        delay = _retry_delay(1)
        base = _RETRY_BASE_DELAY * (2**1)
        assert base * (1 - _RETRY_JITTER) <= delay <= base * (1 + _RETRY_JITTER)

    def test_returns_float(self) -> None:
        """_retry_delay always returns a float."""
        assert isinstance(_retry_delay(0), float)


class TestRaiseForStatus:
    def test_200_does_not_raise(self) -> None:
        """HTTP 200 must not raise any exception."""
        _raise_for_status(_resp(200), "rw/test")

    def test_204_does_not_raise(self) -> None:
        """HTTP 204 must not raise any exception."""
        _raise_for_status(_resp(204), "rw/test")

    def test_401_raises_auth_error(self) -> None:
        """HTTP 401 must raise RWSAuthenticationError."""
        with pytest.raises(RWSAuthenticationError):
            _raise_for_status(_resp(401), "rw/test")

    def test_404_raises_not_found_with_path(self) -> None:
        """HTTP 404 must raise RWSNotFoundError carrying the request path."""
        with pytest.raises(RWSNotFoundError) as exc_info:
            _raise_for_status(_resp(404), "rw/rapid/symbol")
        assert "rw/rapid/symbol" in exc_info.value.resource

    def test_403_raises_http_error(self) -> None:
        """HTTP 403 must raise RWSHTTPError with the correct status code."""
        with pytest.raises(RWSHTTPError) as exc_info:
            _raise_for_status(_resp(403), "rw/test")
        assert exc_info.value.status_code == 403

    def test_500_raises_http_error(self) -> None:
        """HTTP 500 must raise RWSHTTPError with the correct status code."""
        with pytest.raises(RWSHTTPError) as exc_info:
            _raise_for_status(_resp(500), "rw/test")
        assert exc_info.value.status_code == 500

    def test_400_raises_http_error(self) -> None:
        """HTTP 400 must raise RWSHTTPError with the correct status code."""
        with pytest.raises(RWSHTTPError) as exc_info:
            _raise_for_status(_resp(400), "rw/test")
        assert exc_info.value.status_code == 400


# ===========================================================================
# RWSClient — async
# ===========================================================================


class TestClientLifecycle:
    async def test_context_manager_opens_and_closes(self) -> None:
        """Async context manager must open the session on enter and close it on exit."""
        async with RWSClient(host="192.168.125.1") as client:
            assert client._http is not None
        assert client._http is None

    async def test_aopen_idempotent(self) -> None:
        """Calling aopen() twice must not replace the existing httpx client."""
        client = RWSClient(host="192.168.125.1")
        await client.aopen()
        http_first = client._http
        await client.aopen()
        assert client._http is http_first
        await client.aclose()

    async def test_aclose_idempotent(self) -> None:
        """Calling aclose() on an already-closed client must be a no-op."""
        client = RWSClient(host="192.168.125.1")
        await client.aopen()
        await client.aclose()
        await client.aclose()
        assert client._http is None

    async def test_request_before_open_raises_runtime_error(self) -> None:
        """Sending a request before aopen() must raise RuntimeError."""
        client = RWSClient(host="192.168.125.1")
        with pytest.raises(RuntimeError, match="not open"):
            await client.get("rw/rapid/execution")

    async def test_repr_open(self) -> None:
        """repr() on an open client must contain 'open' and the host address."""
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        r = repr(client)
        assert "open" in r
        assert "192.168.125.1" in r

    async def test_repr_closed(self) -> None:
        """repr() on a closed client must contain 'closed' and the host address."""
        client = RWSClient(host="192.168.125.1")
        r = repr(client)
        assert "closed" in r
        assert "192.168.125.1" in r

    async def test_custom_port_in_base_url(self) -> None:
        """A custom port must be reflected in the base URL."""
        client = RWSClient(host="10.0.0.1", port=8080)
        assert "8080" in client.base_url

    async def test_custom_credentials_stored(self) -> None:
        """Custom credentials must be stored on the client instance."""
        client = RWSClient(host="10.0.0.1", username="admin", password="secret")
        assert client.username == "admin"
        assert client.password == "secret"


class TestHttpMethods:
    async def test_get_returns_response(self) -> None:
        """get() must return the httpx response on HTTP 200."""
        transport = _RouteTransport({"rw/test": _resp(200, b'{"ok": true}')})
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200

    async def test_get_sends_query_params(self) -> None:
        """get() must forward query parameters to the outgoing request."""
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        await client.get("rw/test", params={"json": "1"})
        sent = transport.requests[0]
        assert "json=1" in str(sent.url)

    async def test_put_sends_form_data(self) -> None:
        """put() must send the correct HTTP method and form-encoded body."""
        transport = _RouteTransport({"rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR": _resp(204)})
        client = await _open_client(transport)
        await client.put(
            "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            data={"value": "42"},
        )
        sent = transport.requests[0]
        assert sent.method == "PUT"
        assert b"value=42" in sent.content

    async def test_post_sends_correct_method(self) -> None:
        """post() must use the POST HTTP method."""
        transport = _RouteTransport({"rw/mastership/request": _resp(204)})
        client = await _open_client(transport)
        await client.post("rw/mastership/request")
        assert transport.requests[0].method == "POST"

    async def test_delete_sends_correct_method(self) -> None:
        """delete() must use the DELETE HTTP method."""
        transport = _RouteTransport({"rw/rapid/tasks/T_ROB1": _resp(204)})
        client = await _open_client(transport)
        await client.delete("rw/rapid/tasks/T_ROB1")
        assert transport.requests[0].method == "DELETE"

    async def test_204_is_valid_response(self) -> None:
        """HTTP 204 must be returned without raising an exception."""
        transport = _RouteTransport({"rw/mastership/release": _resp(204)})
        client = await _open_client(transport)
        response = await client.post("rw/mastership/release")
        assert response.status_code == 204


class TestStatusCodeValidation:
    async def test_401_raises_auth_error(self) -> None:
        """HTTP 401 from the controller must raise RWSAuthenticationError."""
        transport = _RouteTransport({"rw/test": _resp(401)})
        client = await _open_client(transport)
        with pytest.raises(RWSAuthenticationError):
            await client.get("rw/test")

    async def test_404_raises_not_found(self) -> None:
        """HTTP 404 must raise RWSNotFoundError carrying the request path."""
        transport = _RouteTransport({"rw/test": _resp(404)})
        client = await _open_client(transport)
        with pytest.raises(RWSNotFoundError) as exc_info:
            await client.get("rw/test")
        assert "rw/test" in exc_info.value.resource

    async def test_403_raises_http_error(self) -> None:
        """HTTP 403 must raise RWSHTTPError with status_code == 403."""
        transport = _RouteTransport({"rw/test": _resp(403)})
        client = await _open_client(transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await client.get("rw/test")
        assert exc_info.value.status_code == 403

    async def test_500_raises_http_error(self) -> None:
        """HTTP 500 must raise RWSHTTPError with status_code == 500."""
        transport = _RouteTransport({"rw/test": _resp(500)})
        client = await _open_client(transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            await client.get("rw/test")
        assert exc_info.value.status_code == 500

    async def test_200_returns_response(self) -> None:
        """HTTP 200 must be returned without raising an exception."""
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200


class TestRetryPolicy:
    async def test_retry_on_connect_error(self) -> None:
        """ConnectError triggers a retry — success on the second attempt."""
        transport = _SequentialTransport(
            [
                httpx.ConnectError("connection refused"),
                _resp(200),
            ]
        )
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2

    async def test_retry_on_read_timeout(self) -> None:
        """ReadTimeout triggers a retry — success on the second attempt."""
        transport = _SequentialTransport(
            [
                httpx.ReadTimeout("read timeout"),
                _resp(200),
            ]
        )
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200

    async def test_retry_on_pool_timeout(self) -> None:
        """PoolTimeout triggers a retry — success on the second attempt."""
        transport = _SequentialTransport(
            [
                httpx.PoolTimeout("pool timeout"),
                _resp(200),
            ]
        )
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200

    async def test_retry_exhausted_connect_error_raises_connection_error(self) -> None:
        """ConnectError on every attempt must raise RWSConnectionError."""
        transport = _SequentialTransport([httpx.ConnectError("refused")] * _RETRY_MAX_ATTEMPTS)
        client = await _open_client(transport)
        with pytest.raises(RWSConnectionError):
            await client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS

    async def test_retry_exhausted_read_timeout_raises_timeout_error(self) -> None:
        """ReadTimeout on every attempt must raise RWSTimeoutError."""
        transport = _SequentialTransport([httpx.ReadTimeout("timeout")] * _RETRY_MAX_ATTEMPTS)
        client = await _open_client(transport)
        with pytest.raises(RWSTimeoutError):
            await client.get("rw/test")

    async def test_retry_exhausted_pool_timeout_raises_timeout_error(self) -> None:
        """PoolTimeout on every attempt must raise RWSTimeoutError."""
        transport = _SequentialTransport([httpx.PoolTimeout("pool")] * _RETRY_MAX_ATTEMPTS)
        client = await _open_client(transport)
        with pytest.raises(RWSTimeoutError):
            await client.get("rw/test")

    async def test_http_error_not_retried(self) -> None:
        """An HTTP 500 error must not trigger a retry — exactly 1 request sent."""
        transport = _SequentialTransport([_resp(500), _resp(200)])
        client = await _open_client(transport)
        with pytest.raises(RWSHTTPError):
            await client.get("rw/test")
        assert len(transport.requests) == 1

    async def test_exact_retry_count(self) -> None:
        """Total attempt count must equal _RETRY_MAX_ATTEMPTS exactly."""
        transport = _SequentialTransport([httpx.ConnectError("refused")] * _RETRY_MAX_ATTEMPTS)
        client = await _open_client(transport)
        with pytest.raises(RWSConnectionError):
            await client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS


# ===========================================================================
# RWSClientSync
# ===========================================================================


class TestRWSClientSyncLifecycle:
    def test_context_manager_opens_and_closes(self) -> None:
        """Sync context manager must open the session on enter and close it on exit."""
        with RWSClientSync(host="192.168.125.1") as client:
            assert client._http is not None
        assert client._http is None

    def test_open_idempotent(self) -> None:
        """Calling open() twice must not replace the existing httpx client."""
        client = RWSClientSync(host="192.168.125.1")
        client.open()
        http_first = client._http
        client.open()
        assert client._http is http_first
        client.close()

    def test_close_idempotent(self) -> None:
        """Calling close() on an already-closed client must be a no-op."""
        client = RWSClientSync(host="192.168.125.1")
        client.open()
        client.close()
        client.close()
        assert client._http is None

    def test_request_before_open_raises_runtime_error(self) -> None:
        """Sending a request before open() must raise RuntimeError."""
        client = RWSClientSync(host="192.168.125.1")
        with pytest.raises(RuntimeError, match="not open"):
            client.get("rw/rapid/execution")

    def test_repr_open(self) -> None:
        """repr() on an open client must contain 'open' and the host address."""
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        r = repr(client)
        assert "open" in r
        assert "192.168.125.1" in r

    def test_repr_closed(self) -> None:
        """repr() on a closed client must contain 'closed'."""
        client = RWSClientSync(host="192.168.125.1")
        r = repr(client)
        assert "closed" in r


class TestRWSClientSyncHttpMethods:
    def test_get_returns_response(self) -> None:
        """get() must return the httpx response on HTTP 200."""
        transport = _RouteSyncTransport({"rw/test": _resp(200, b'{"ok": true}')})
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200

    def test_get_sends_query_params(self) -> None:
        """get() must forward query parameters to the outgoing request."""
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        client.get("rw/test", params={"json": "1"})
        sent = transport.requests[0]
        assert "json=1" in str(sent.url)

    def test_put_sends_form_data(self) -> None:
        """put() must send the correct HTTP method and form-encoded body."""
        transport = _RouteSyncTransport({"rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR": _resp(204)})
        client = _open_sync_client(transport)
        client.put(
            "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            data={"value": "42"},
        )
        sent = transport.requests[0]
        assert sent.method == "PUT"
        assert b"value=42" in sent.content

    def test_post_sends_correct_method(self) -> None:
        """post() must use the POST HTTP method."""
        transport = _RouteSyncTransport({"rw/mastership/request": _resp(204)})
        client = _open_sync_client(transport)
        client.post("rw/mastership/request")
        assert transport.requests[0].method == "POST"

    def test_delete_sends_correct_method(self) -> None:
        """delete() must use the DELETE HTTP method."""
        transport = _RouteSyncTransport({"rw/rapid/tasks/T_ROB1": _resp(204)})
        client = _open_sync_client(transport)
        client.delete("rw/rapid/tasks/T_ROB1")
        assert transport.requests[0].method == "DELETE"

    def test_204_is_valid_response(self) -> None:
        """HTTP 204 must be returned without raising an exception."""
        transport = _RouteSyncTransport({"rw/mastership/release": _resp(204)})
        client = _open_sync_client(transport)
        response = client.post("rw/mastership/release")
        assert response.status_code == 204


class TestRWSClientSyncStatusCodes:
    def test_401_raises_auth_error(self) -> None:
        """HTTP 401 from the controller must raise RWSAuthenticationError."""
        transport = _RouteSyncTransport({"rw/test": _resp(401)})
        client = _open_sync_client(transport)
        with pytest.raises(RWSAuthenticationError):
            client.get("rw/test")

    def test_404_raises_not_found(self) -> None:
        """HTTP 404 must raise RWSNotFoundError carrying the request path."""
        transport = _RouteSyncTransport({"rw/test": _resp(404)})
        client = _open_sync_client(transport)
        with pytest.raises(RWSNotFoundError) as exc_info:
            client.get("rw/test")
        assert "rw/test" in exc_info.value.resource

    def test_500_raises_http_error(self) -> None:
        """HTTP 500 must raise RWSHTTPError with status_code == 500."""
        transport = _RouteSyncTransport({"rw/test": _resp(500)})
        client = _open_sync_client(transport)
        with pytest.raises(RWSHTTPError) as exc_info:
            client.get("rw/test")
        assert exc_info.value.status_code == 500


class TestRWSClientSyncRetryPolicy:
    def test_retry_on_connect_error(self) -> None:
        """ConnectError triggers a retry — success on the second attempt."""
        transport = _SequentialSyncTransport(
            [
                httpx.ConnectError("refused"),
                _resp(200),
            ]
        )
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2

    def test_retry_on_read_timeout(self) -> None:
        """ReadTimeout triggers a retry — success on the second attempt."""
        transport = _SequentialSyncTransport(
            [
                httpx.ReadTimeout("timeout"),
                _resp(200),
            ]
        )
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200

    def test_retry_on_pool_timeout(self) -> None:
        """PoolTimeout triggers a retry — success on the second attempt."""
        transport = _SequentialSyncTransport(
            [
                httpx.PoolTimeout("pool"),
                _resp(200),
            ]
        )
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200

    def test_retry_exhausted_connect_error_raises_connection_error(self) -> None:
        """ConnectError on every attempt must raise RWSConnectionError."""
        transport = _SequentialSyncTransport([httpx.ConnectError("refused")] * _RETRY_MAX_ATTEMPTS)
        client = _open_sync_client(transport)
        with pytest.raises(RWSConnectionError):
            client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS

    def test_retry_exhausted_timeout_raises_timeout_error(self) -> None:
        """ReadTimeout on every attempt must raise RWSTimeoutError."""
        transport = _SequentialSyncTransport([httpx.ReadTimeout("timeout")] * _RETRY_MAX_ATTEMPTS)
        client = _open_sync_client(transport)
        with pytest.raises(RWSTimeoutError):
            client.get("rw/test")

    def test_http_error_not_retried(self) -> None:
        """An HTTP 500 error must not trigger a retry — exactly 1 request sent."""
        transport = _SequentialSyncTransport([_resp(500), _resp(200)])
        client = _open_sync_client(transport)
        with pytest.raises(RWSHTTPError):
            client.get("rw/test")
        assert len(transport.requests) == 1


class TestHttpMethodsHeadOptions:
    """Tests for head() and options() — async."""

    async def test_head_sends_correct_method(self) -> None:
        """head() must use the HEAD HTTP method."""
        transport = _RouteTransport({"rw/fileservice/test.txt": _resp(200)})
        client = await _open_client(transport)
        await client.head("rw/fileservice/test.txt")
        assert transport.requests[0].method == "HEAD"

    async def test_head_returns_response(self) -> None:
        """head() must return the httpx response on HTTP 200."""
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        response = await client.head("rw/test")
        assert response.status_code == 200

    async def test_options_sends_correct_method(self) -> None:
        """options() must use the OPTIONS HTTP method."""
        transport = _RouteTransport({"ctrl/network/route/add": _resp(200)})
        client = await _open_client(transport)
        await client.options("ctrl/network/route/add")
        assert transport.requests[0].method == "OPTIONS"

    async def test_options_returns_response(self) -> None:
        """options() must return the httpx response on HTTP 200."""
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        response = await client.options("rw/test")
        assert response.status_code == 200


class TestContentTypeInjection:
    """Tests for the automatic Content-Type injection on POST/PUT — async."""

    async def test_post_without_content_type_gets_form_urlencoded(self) -> None:
        """POST without explicit Content-Type must receive
        application/x-www-form-urlencoded."""
        transport = _RouteTransport({"rw/test": _resp(204)})
        client = await _open_client(transport)
        await client.post("rw/test")
        sent = transport.requests[0]
        ct = sent.headers.get("content-type", "")
        assert "application/x-www-form-urlencoded" in ct

    async def test_put_without_content_type_gets_form_urlencoded(self) -> None:
        """PUT without explicit Content-Type must receive
        application/x-www-form-urlencoded."""
        transport = _RouteTransport({"rw/test": _resp(204)})
        client = await _open_client(transport)
        await client.put("rw/test", data={"value": "1"})
        sent = transport.requests[0]
        ct = sent.headers.get("content-type", "")
        assert "application/x-www-form-urlencoded" in ct

    async def test_post_with_existing_content_type_is_not_overwritten(self) -> None:
        """POST with an explicit Content-Type must not be overwritten."""
        transport = _RouteTransport({"rw/test": _resp(204)})
        client = await _open_client(transport)
        await client.post(
            "rw/test",
            headers={"Content-Type": "application/json"},
            content=b"{}",
        )
        sent = transport.requests[0]
        ct = sent.headers.get("content-type", "")
        assert "application/json" in ct

    async def test_get_does_not_get_content_type_injected(self) -> None:
        """GET requests must NOT receive an injected Content-Type."""
        transport = _RouteTransport({"rw/test": _resp(200)})
        client = await _open_client(transport)
        await client.get("rw/test")
        sent = transport.requests[0]
        assert "content-type" not in {k.lower() for k in dict(sent.headers)}


class TestRetryPolicyConnectTimeout:
    """ConnectTimeout retry coverage — async."""

    async def test_retry_on_connect_timeout(self) -> None:
        """ConnectTimeout triggers a retry — success on the second attempt."""
        transport = _SequentialTransport(
            [
                httpx.ConnectTimeout("connect timeout"),
                _resp(200),
            ]
        )
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2

    async def test_retry_exhausted_connect_timeout_raises_timeout_error(
        self,
    ) -> None:
        """ConnectTimeout on every attempt must raise RWSTimeoutError."""
        transport = _SequentialTransport(
            [httpx.ConnectTimeout("connect timeout")] * _RETRY_MAX_ATTEMPTS
        )
        client = await _open_client(transport)
        with pytest.raises(RWSTimeoutError):
            await client.get("rw/test")


class TestRWSClientSyncHttpMethodsHeadOptions:
    """Tests for head() and options() — sync."""

    def test_head_sends_correct_method(self) -> None:
        """head() must use the HEAD HTTP method."""
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        client.head("rw/test")
        assert transport.requests[0].method == "HEAD"

    def test_head_returns_response(self) -> None:
        """head() must return the httpx response on HTTP 200."""
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        response = client.head("rw/test")
        assert response.status_code == 200

    def test_options_sends_correct_method(self) -> None:
        """options() must use the OPTIONS HTTP method."""
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        client.options("rw/test")
        assert transport.requests[0].method == "OPTIONS"

    def test_options_returns_response(self) -> None:
        """options() must return the httpx response on HTTP 200."""
        transport = _RouteSyncTransport({"rw/test": _resp(200)})
        client = _open_sync_client(transport)
        response = client.options("rw/test")
        assert response.status_code == 200


class TestRWSClientSyncContentTypeInjection:
    """Tests for the automatic Content-Type injection on POST/PUT — sync."""

    def test_post_without_content_type_gets_form_urlencoded(self) -> None:
        """POST without explicit Content-Type must receive
        application/x-www-form-urlencoded."""
        transport = _RouteSyncTransport({"rw/test": _resp(204)})
        client = _open_sync_client(transport)
        client.post("rw/test")
        sent = transport.requests[0]
        ct = sent.headers.get("content-type", "")
        assert "application/x-www-form-urlencoded" in ct

    def test_put_without_content_type_gets_form_urlencoded(self) -> None:
        """PUT without explicit Content-Type must receive
        application/x-www-form-urlencoded."""
        transport = _RouteSyncTransport({"rw/test": _resp(204)})
        client = _open_sync_client(transport)
        client.put("rw/test", data={"value": "1"})
        sent = transport.requests[0]
        ct = sent.headers.get("content-type", "")
        assert "application/x-www-form-urlencoded" in ct

    def test_post_with_existing_content_type_is_not_overwritten(self) -> None:
        """POST with an explicit Content-Type must not be overwritten."""
        transport = _RouteSyncTransport({"rw/test": _resp(204)})
        client = _open_sync_client(transport)
        client.post(
            "rw/test",
            headers={"Content-Type": "application/json"},
            content=b"{}",
        )
        sent = transport.requests[0]
        ct = sent.headers.get("content-type", "")
        assert "application/json" in ct


class TestRWSClientSyncRetryPolicyConnectTimeout:
    """ConnectTimeout retry coverage — sync."""

    def test_retry_on_connect_timeout(self) -> None:
        """ConnectTimeout triggers a retry — success on the second attempt."""
        transport = _SequentialSyncTransport(
            [
                httpx.ConnectTimeout("connect timeout"),
                _resp(200),
            ]
        )
        client = _open_sync_client(transport)
        response = client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2

    def test_retry_exhausted_connect_timeout_raises_timeout_error(self) -> None:
        """ConnectTimeout on every attempt must raise RWSTimeoutError."""
        transport = _SequentialSyncTransport(
            [httpx.ConnectTimeout("connect timeout")] * _RETRY_MAX_ATTEMPTS
        )
        client = _open_sync_client(transport)
        with pytest.raises(RWSTimeoutError):
            client.get("rw/test")