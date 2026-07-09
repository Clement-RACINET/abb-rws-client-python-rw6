# tests/test_client.py
"""
Tests unitaires pour RWSClient — utilise httpx.MockTransport, aucun robot requis.

Couverture ciblée :
- Cycle de vie : aopen / aclose / context manager / idempotence
- Méthodes HTTP : get / put / post
- Politique de retry : déclencheurs, comptage, délai
- Validation status codes : 200, 204, 401, 404, 4xx, 5xx
- Erreurs transport → exceptions RWS custom
- __repr__
"""

from __future__ import annotations

import httpx
import pytest

from abb_rws_client.client import _RETRY_MAX_ATTEMPTS, RWSClient
from abb_rws_client.exceptions import (
    RWSAuthenticationError,
    RWSConnectionError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
)

# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------


def _resp(status_code: int, content: bytes = b"{}") -> httpx.Response:
    """Crée une réponse httpx minimale."""
    return httpx.Response(status_code=status_code, content=content)


class _SequentialTransport(httpx.AsyncBaseTransport):
    """Retourne les réponses dans l'ordre de la liste fournie.

    Utile pour simuler : échec → échec → succès (test retry).
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
    """Retourne une réponse fixe par chemin URL."""

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        self._routes = routes
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


def _inject(client: RWSClient, transport: httpx.AsyncBaseTransport) -> RWSClient:
    """Injecte un transport mocké dans un RWSClient déjà ouvert."""
    client._http = httpx.AsyncClient(
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


# ---------------------------------------------------------------------------
# Cycle de vie
# ---------------------------------------------------------------------------


class TestClientLifecycle:
    async def test_context_manager_opens_and_closes(self) -> None:
        async with RWSClient(host="192.168.125.1") as client:
            assert client._http is not None
        assert client._http is None

    async def test_aopen_idempotent(self) -> None:
        """Appeler aopen() deux fois ne lève pas d'erreur."""
        client = RWSClient(host="192.168.125.1")
        await client.aopen()
        http_first = client._http
        await client.aopen()  # deuxième appel — doit être no-op
        assert client._http is http_first  # même instance
        await client.aclose()

    async def test_aclose_idempotent(self) -> None:
        """Appeler aclose() deux fois ne lève pas d'erreur."""
        client = RWSClient(host="192.168.125.1")
        await client.aopen()
        await client.aclose()
        await client.aclose()  # deuxième appel — doit être no-op
        assert client._http is None

    async def test_request_before_open_raises_runtime_error(self) -> None:
        """Requête sans aopen() → RuntimeError explicite."""
        client = RWSClient(host="192.168.125.1")
        with pytest.raises(RuntimeError, match="not open"):
            await client.get("rw/rapid/execution")


# ---------------------------------------------------------------------------
# Méthodes HTTP
# ---------------------------------------------------------------------------


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
        transport = _RouteTransport({"rw/mastership/request": _resp(204)})
        client = await _open_client(transport)
        await client.post("rw/mastership/request")
        assert transport.requests[0].method == "POST"

    async def test_204_is_valid_response(self) -> None:
        """204 No Content est une réponse valide pour les actions RWS."""
        transport = _RouteTransport({"rw/mastership/release": _resp(204)})
        client = await _open_client(transport)
        response = await client.post("rw/mastership/release")
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# Validation des status codes
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Politique de retry
# ---------------------------------------------------------------------------


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

    async def test_retry_exhausted_connect_error_raises_connection_error(self) -> None:
        """Après épuisement des retries sur ConnectError → RWSConnectionError."""
        transport = _SequentialTransport([
            httpx.ConnectError("refused") for _ in range(_RETRY_MAX_ATTEMPTS)
        ])
        client = await _open_client(transport)
        with pytest.raises(RWSConnectionError, match="Connection failed"):
            await client.get("rw/test")
        assert len(transport.requests) == _RETRY_MAX_ATTEMPTS

    async def test_retry_exhausted_read_timeout_raises_timeout_error(self) -> None:
        """Après épuisement des retries sur ReadTimeout → RWSTimeoutError."""
        transport = _SequentialTransport([
            httpx.ReadTimeout("timeout") for _ in range(_RETRY_MAX_ATTEMPTS)
        ])
        client = await _open_client(transport)
        with pytest.raises(RWSTimeoutError, match="Timeout"):
            await client.get("rw/test")

    async def test_no_retry_on_404(self) -> None:
        """Les erreurs HTTP ne déclenchent pas de retry."""
        transport = _SequentialTransport([_resp(404)])
        client = await _open_client(transport)
        with pytest.raises(RWSNotFoundError):
            await client.get("rw/test")
        # Une seule requête — pas de retry
        assert len(transport.requests) == 1

    async def test_no_retry_on_401(self) -> None:
        """401 ne déclenche pas de retry."""
        transport = _SequentialTransport([_resp(401)])
        client = await _open_client(transport)
        with pytest.raises(RWSAuthenticationError):
            await client.get("rw/test")
        assert len(transport.requests) == 1

    async def test_connect_timeout_triggers_retry(self) -> None:
        """ConnectTimeout (distinct de ReadTimeout dans httpx) déclenche aussi un retry."""
        transport = _SequentialTransport([
            httpx.ConnectTimeout("connect timeout"),
            _resp(200),
        ])
        client = await _open_client(transport)
        response = await client.get("rw/test")
        assert response.status_code == 200
        assert len(transport.requests) == 2


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestClientRepr:
    async def test_repr_closed(self) -> None:
        client = RWSClient(host="192.168.125.1", username="Default User", timeout=10.0)
        assert "closed" in repr(client)
        assert "192.168.125.1" in repr(client)

    async def test_repr_open(self) -> None:
        async with RWSClient(host="192.168.125.1") as client:
            assert "open" in repr(client)

    async def test_repr_contains_timeout(self) -> None:
        client = RWSClient(host="192.168.125.1", timeout=30.0)
        assert "30.0" in repr(client)
