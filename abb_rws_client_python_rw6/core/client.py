# abb_rws_client/core/client.py
"""
HTTP session management for an ABB RWS controller (RobotWare 6).

Author: Clement RACINET

Module responsibilities:
- Create and maintain an httpx.AsyncClient configured for RWS
- Handle ABB HTTP Digest authentication
- Maintain the ABBCX session cookie
- Expose low-level HTTP methods (get, put, post, delete, head, options)
  used by the rws/ and highlevel/ modules
- Implement the retry policy on transport errors
- Provide RWSClientSync, a synchronous wrapper with no logic duplication

Retry policy (documented here, implemented in _request)::

    - Triggers: ConnectError, ConnectTimeout, ReadTimeout, PoolTimeout only.
      HTTP errors (4xx, 5xx) are never retried.
    - Attempts: 3 total (1 initial attempt + 2 retries)
    - Delay: exponential with ±10% jitter
      base * 2^attempt + jitter  →  ~0.5s, ~1s, ~2s

ABBCX cookie management::

    httpx.AsyncClient maintains this cookie natively via its cookiejar.
    On expiry (ABB timeout ~10 min), the controller responds with 401
    and httpx.DigestAuth automatically restarts the handshake.

RWSClientSync::

    Synchronous wrapper based on httpx.Client (httpx native sync).
    Same retry/auth logic, no anyio dependency at runtime.
    All methods are synchronous (no async def).
"""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType
from typing import Any, Self

import httpx

from abb_rws_client_python_rw6.core.env import get_env_float_or_none, get_env_int, get_env_str
from abb_rws_client_python_rw6.core.exceptions import (
    RWSAuthenticationError,
    RWSConnectionError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry constants
# ---------------------------------------------------------------------------

#: Total number of attempts (1 initial attempt + _RETRY_MAX_ATTEMPTS - 1 retries)
_RETRY_MAX_ATTEMPTS: int = 3

#: Base delay in seconds: _RETRY_BASE_DELAY * 2^attempt → 0.5s, 1.0s, 2.0s
_RETRY_BASE_DELAY: float = 0.5

#: Jitter amplitude (fraction of the computed delay) → ±10%
_RETRY_JITTER: float = 0.1

#: httpx exception types that trigger a retry (transport errors only)
_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.PoolTimeout,
)

# ---------------------------------------------------------------------------
# Shared helpers (async/sync)
# ---------------------------------------------------------------------------


def _build_auth(username: str, password: str) -> httpx.DigestAuth:
    """Build the httpx DigestAuth object.

    Args:
        username: RWS username.
        password: RWS password.

    Returns:
        Configured ``httpx.DigestAuth`` instance.

    Example:
        ```python
        >>> auth = _build_auth("Default User", "robotics")
        ```
    """
    return httpx.DigestAuth(username, password)


def _raise_for_status(response: httpx.Response, path: str) -> None:
    """Raise the appropriate RWS exception based on the HTTP status code.

    Args:
        response: The httpx response received.
        path: Request path, used in error messages.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other status >= 400.

    Example:
        ```python
        >>> _raise_for_status(response, "rw/rapid/execution")
        ```
    """
    code = response.status_code
    if code == 401:
        raise RWSAuthenticationError()
    if code == 404:
        raise RWSNotFoundError(path)
    # ── _raise_for_status : 200 → 1000 ────────────────────────────────────────
    if code >= 400:
        raise RWSHTTPError(
            f"HTTP {code} on {path}: {response.text[:1000]}",  # était 200
            status_code=code,
        )


def _retry_delay(attempt: int) -> float:
    """Compute the delay before the next retry, with exponential backoff and jitter.

    Args:
        attempt: Index of the failed attempt (0-based).

    Returns:
        Delay in seconds (float).

    Example:
        ```python
        >>> delay = _retry_delay(0)  # ~0.5s
        >>> delay = _retry_delay(1)  # ~1.0s
        ```
    """
    base = _RETRY_BASE_DELAY * (2**attempt)
    jitter = base * _RETRY_JITTER * (2 * random.random() - 1)
    return base + jitter


# ---------------------------------------------------------------------------
# RWSClient — async
# ---------------------------------------------------------------------------


class RWSClient:
    """Async HTTP client for the ABB Robot Web Services (RWS) API — RobotWare 6.

    Designed to be used as an async context manager, which guarantees
    proper HTTP session teardown in all cases.

    Args:
        host: Controller IP address or hostname (e.g. ``"192.168.125.1"``).
        username: RWS username (ABB default: ``"Default User"``).
        password: RWS password (ABB default: ``"robotics"``).
        port: Controller HTTP port (default: ``80``).
        timeout: HTTP timeout in seconds, or ``None`` for no timeout (default: ``None``).

    Example:
        ```python
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     resp = await client.get("rw/rapid/execution")
        ```
    """

    def __init__(
        self,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self.host     = host     or get_env_str("RWS_HOST",     "192.168.125.1")
        self.username = username or get_env_str("RWS_USER",     "Default User")
        self.password = password or get_env_str("RWS_PASSWORD", "robotics")
        self.port     = port     or get_env_int("RWS_PORT",     80)
        self.timeout = (
            timeout if timeout is not None else get_env_float_or_none("RWS_TIMEOUT", None)
        )
        self.base_url = f"http://{self.host}:{self.port}/"
        self._http: httpx.AsyncClient | None = None

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def aopen(self) -> None:
        """Open the HTTP session. Idempotent: no-op if already open.

        Raises:
            RWSConnectionError: If the initial connection fails.

        Example:
            ```python
            >>> await client.aopen()
            ```
        """
        if self._http is not None:
            return
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            auth=_build_auth(self.username, self.password),
            timeout=self.timeout,
            follow_redirects=True,
        )
        logger.debug("RWSClient opened → %s", self.base_url)

    async def aclose(self) -> None:
        """Close the HTTP session. Idempotent: no-op if already closed.

        Example:
            ```python
            >>> await client.aclose()
            ```
        """
        if self._http is None:
            return
        await self._http.aclose()
        self._http = None
        logger.debug("RWSClient closed → %s", self.base_url)

    async def __aenter__(self) -> Self:
        await self.aopen()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        state = "open" if self._http is not None else "closed"
        return f"RWSClient(host={self.host!r}, timeout={self.timeout}, state={state!r})"

    # ── Internal request with retry ─────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute an HTTP request with the transport-error retry policy.

        Args:
            method: HTTP method (``"GET"``, ``"POST"``, ``"PUT"``, ``"DELETE"``).
            path: Path relative to the base URL (e.g. ``"rw/rapid/execution"``).
            **kwargs: Additional parameters forwarded to httpx
                (``params``, ``data``, ``json``, …).

        Returns:
            httpx response (status not checked — call ``_raise_for_status``
            if needed, though it is already called internally).

        Raises:
            RuntimeError: If the client is not open.
            RWSConnectionError: After retries are exhausted on ConnectError.
            RWSTimeoutError: After retries are exhausted on ReadTimeout/PoolTimeout.
            RWSAuthenticationError: On HTTP 401.
            RWSNotFoundError: On HTTP 404.
            RWSHTTPError: On any other HTTP >= 400.

        Example:
            ```python
            >>> resp = await client._request(
            ...     "GET",
            ...     "rw/rapid/execution",
            ...     params={"json": "1"},
            ... )
            ```
        """
        if self._http is None:
            raise RuntimeError(
                "RWSClient is not open. Use 'async with RWSClient(...) as client' "
                "or call await client.aopen() first."
            )

        # ABB RW6 requires Content-Type: application/x-www-form-urlencoded on
        # every POST and PUT, even when the body is empty. httpx does not set
        # this header automatically when data={} or no body is provided.
        if method in ("POST", "PUT"):
            headers: dict[str, str] = dict(kwargs.pop("headers", None) or {})
            if "content-type" not in {k.lower() for k in headers}:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            kwargs["headers"] = headers

        last_exc: Exception | None = None
        for attempt in range(_RETRY_MAX_ATTEMPTS):
            try:
                response = await self._http.request(method, path, **kwargs)
                _raise_for_status(response, path)
                return response
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < _RETRY_MAX_ATTEMPTS - 1:
                    delay = _retry_delay(attempt)
                    logger.warning(
                        "RWSClient %s %s → %s (attempt %d/%d, retry in %.2fs)",
                        method,
                        path,
                        type(exc).__name__,
                        attempt + 1,
                        _RETRY_MAX_ATTEMPTS,
                        delay,
                    )
                    await asyncio.sleep(delay)
        # All retries exhausted
        assert last_exc is not None
        if isinstance(last_exc, httpx.ConnectError):
            raise RWSConnectionError(
                f"Connection failed to {self.base_url}: {last_exc}"
            ) from last_exc
        raise RWSTimeoutError(
            f"Timeout on {method} {path} after {_RETRY_MAX_ATTEMPTS} attempts"
        ) from last_exc

    # ── Public HTTP methods ──────────────────────────────────────────────────

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send an HTTP GET request to the RWS controller.

        Route: ``GET {path}``

        Args:
            path: Path relative to the base URL (e.g. ``"rw/rapid/execution"``).
            **kwargs: Additional httpx parameters (``params``, ``headers``, …).

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> resp = await client.get("rw/rapid/execution", params={"json": "1"})
            ```
        """
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send an HTTP POST request to the RWS controller.

        Route: ``POST {path}``

        Args:
            path: Path relative to the base URL (e.g. ``"rw/mastership"``).
            **kwargs: Additional httpx parameters (``params``, ``data``, ``json``, …).

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> await client.post("rw/mastership", params={"action": "request"})
            ```
        """
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send an HTTP PUT request to the RWS controller.

        Route: ``PUT {path}`` — typically used to write a RAPID variable.

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional httpx parameters (``data``, …).

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> await client.put(
            ...     "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            ...     data={"value": "42"},
            ... )
            ```
        """
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send an HTTP DELETE request to the RWS controller.

        Route: ``DELETE {path}`` — typically used for fileservice or elog resources.

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional httpx parameters.

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> await client.delete("fileservice/$HOME/old_backup.tar.gz")
            ```
        """
        return await self._request("DELETE", path, **kwargs)

    async def head(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an HTTP HEAD request to the RWS controller.

        Route: ``HEAD {path}``

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional parameters forwarded to httpx.

        Returns:
            Raw HTTP response (headers only, no body).

        Raises:
            RWSAuthenticationError: On HTTP 401.
            RWSNotFoundError: On HTTP 404.
            RWSHTTPError: On any other HTTP >= 400.
            RWSConnectionError: If the controller is unreachable.
            RWSTimeoutError: If the request exceeds the timeout.

        Example:
            ```python
            >>> resp = await client.head("fileservice/$HOME/myfile.txt")
            ```
        """
        return await self._request("HEAD", path, **kwargs)

    async def options(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an HTTP OPTIONS request to the RWS controller.

        Route: ``OPTIONS {path}``

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional parameters forwarded to httpx.

        Returns:
            Raw HTTP response.

        Raises:
            RWSAuthenticationError: On HTTP 401.
            RWSNotFoundError: On HTTP 404.
            RWSHTTPError: On any other HTTP >= 400.
            RWSConnectionError: If the controller is unreachable.
            RWSTimeoutError: If the request exceeds the timeout.

        Example:
            ```python
            >>> resp = await client.options("ctrl/network/route/add")
            ```
        """
        return await self._request("OPTIONS", path, **kwargs)


# ---------------------------------------------------------------------------
# RWSClientSync — synchronous wrapper
# ---------------------------------------------------------------------------


class RWSClientSync:
    """Synchronous HTTP client for the ABB RWS API — RobotWare 6.

    Synchronous wrapper around ``RWSClient``, based on ``httpx.Client`` natively.
    Same authentication policy (DigestAuth), same retry logic, same error handling.
    No ``anyio`` or ``asyncio`` dependency at runtime.

    Designed to be used as a synchronous context manager.

    Args:
        host: Controller IP address or hostname (e.g. ``"192.168.125.1"``).
            Reads ``RWS_HOST`` from environment if ``None``.
        username: RWS username (ABB default: ``"Default User"``).
            Reads ``RWS_USER`` from environment if ``None``.
        password: RWS password (ABB default: ``"robotics"``).
            Reads ``RWS_PASSWORD`` from environment if ``None``.
        port: HTTP port (default: ``80``).
            Reads ``RWS_PORT`` from environment if ``None``.
        timeout: HTTP timeout in seconds, or ``None`` for no timeout
            (default: ``None``). Reads ``RWS_TIMEOUT`` from environment
            if not provided explicitly.

    Example:
        ```python
        >>> with RWSClientSync(host="192.168.125.1") as client:
        ...     resp = client.get("rw/rapid/execution")
        ```
    """

    def __init__(
        self,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self.host     = host     or get_env_str("RWS_HOST",     "192.168.125.1")
        self.username = username or get_env_str("RWS_USER",     "Default User")
        self.password = password or get_env_str("RWS_PASSWORD", "robotics")
        self.port     = port     or get_env_int("RWS_PORT",     80)
        self.timeout = (
            timeout if timeout is not None else get_env_float_or_none("RWS_TIMEOUT", None)
        )
        self.base_url = f"http://{self.host}:{self.port}/"
        self._http: httpx.Client | None = None

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def open(self) -> None:
        """Open the HTTP session. Idempotent: no-op if already open.

        Example:
            ```python
            >>> client.open()
            ```
        """
        if self._http is not None:
            return
        self._http = httpx.Client(
            base_url=self.base_url,
            auth=_build_auth(self.username, self.password),
            timeout=self.timeout,
            follow_redirects=True,
        )
        logger.debug("RWSClientSync opened → %s", self.base_url)

    def close(self) -> None:
        """Close the HTTP session. Idempotent: no-op if already closed.

        Example:
            ```python
            >>> client.close()
            ```
        """
        if self._http is None:
            return
        self._http.close()
        self._http = None
        logger.debug("RWSClientSync closed → %s", self.base_url)

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        state = "open" if self._http is not None else "closed"
        return f"RWSClientSync(host={self.host!r}, state={state!r})"

    # ── Internal request with retry ─────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Execute a synchronous HTTP request with the transport-error retry policy.

        Args:
            method: HTTP method (``"GET"``, ``"POST"``, ``"PUT"``, ``"DELETE"``).
            path: Path relative to the base URL.
            **kwargs: Additional parameters forwarded to httpx.

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RuntimeError: If the client is not open.
            RWSConnectionError: After retries are exhausted on ConnectError.
            RWSTimeoutError: After retries are exhausted on timeout errors.
            RWSAuthenticationError: On HTTP 401.
            RWSNotFoundError: On HTTP 404.
            RWSHTTPError: On any other HTTP >= 400.

        Example:
            ```python
            >>> resp = client._request(
            ...     "GET",
            ...     "rw/rapid/execution",
            ...     params={"json": "1"},
            ... )
            ```
        """
        if self._http is None:
            raise RuntimeError(
                "RWSClientSync is not open. Use 'with RWSClientSync(...) as client' "
                "or call client.open() first."
            )

        # ABB RW6 requires Content-Type: application/x-www-form-urlencoded on
        # every POST and PUT, even when the body is empty. httpx does not set
        # this header automatically when data={} or no body is provided.
        if method in ("POST", "PUT"):
            headers: dict[str, str] = dict(kwargs.pop("headers", None) or {})
            if "content-type" not in {k.lower() for k in headers}:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            kwargs["headers"] = headers

        import time

        last_exc: Exception | None = None
        for attempt in range(_RETRY_MAX_ATTEMPTS):
            try:
                response = self._http.request(method, path, **kwargs)
                _raise_for_status(response, path)
                return response
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < _RETRY_MAX_ATTEMPTS - 1:
                    delay = _retry_delay(attempt)
                    logger.warning(
                        "RWSClientSync %s %s → %s (attempt %d/%d, retry in %.2fs)",
                        method,
                        path,
                        type(exc).__name__,
                        attempt + 1,
                        _RETRY_MAX_ATTEMPTS,
                        delay,
                    )
                    time.sleep(delay)
        # All retries exhausted
        assert last_exc is not None
        if isinstance(last_exc, httpx.ConnectError):
            raise RWSConnectionError(
                f"Cannot connect to {self.base_url}: {last_exc}"
            ) from last_exc
        raise RWSTimeoutError(
            f"Timeout on {method} {path} after {_RETRY_MAX_ATTEMPTS} attempts"
        ) from last_exc

    # ── Public HTTP methods ──────────────────────────────────────────────────

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a synchronous HTTP GET request to the RWS controller.

        Route: ``GET {path}``

        Args:
            path: Path relative to the base URL (e.g. ``"rw/rapid/execution"``).
            **kwargs: Additional httpx parameters (``params``, …).

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> resp = client.get("rw/rapid/execution", params={"json": "1"})
            ```
        """
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a synchronous HTTP POST request to the RWS controller.

        Route: ``POST {path}``

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional httpx parameters (``params``, ``data``, …).

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> client.post("rw/mastership", params={"action": "request"})
            ```
        """
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a synchronous HTTP PUT request to the RWS controller.

        Route: ``PUT {path}`` — typically used to write a RAPID variable.

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional httpx parameters (``data``, …).

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> client.put(
            ...     "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            ...     data={"value": "42"},
            ... )
            ```
        """
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a synchronous HTTP DELETE request to the RWS controller.

        Route: ``DELETE {path}``

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional httpx parameters.

        Returns:
            Validated httpx response (status < 400).

        Raises:
            RWSConnectionError: Network error after retries.
            RWSTimeoutError: Timeout after retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Any other HTTP >= 400.

        Example:
            ```python
            >>> client.delete("fileservice/$HOME/old_backup.tar.gz")
            ```
        """
        return self._request("DELETE", path, **kwargs)

    def head(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a synchronous HTTP HEAD request to the RWS controller.

        Route: ``HEAD {path}``

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional parameters forwarded to httpx.

        Returns:
            Raw HTTP response (headers only, no body).

        Raises:
            RWSAuthenticationError: On HTTP 401.
            RWSNotFoundError: On HTTP 404.
            RWSHTTPError: On any other HTTP >= 400.
            RWSConnectionError: If the controller is unreachable.
            RWSTimeoutError: If the request exceeds the timeout.

        Example:
            ```python
            >>> resp = client.head("fileservice/$HOME/myfile.txt")
            ```
        """
        return self._request("HEAD", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a synchronous HTTP OPTIONS request to the RWS controller.

        Route: ``OPTIONS {path}``

        Args:
            path: Path relative to the base URL.
            **kwargs: Additional parameters forwarded to httpx.

        Returns:
            Raw HTTP response.

        Raises:
            RWSAuthenticationError: On HTTP 401.
            RWSNotFoundError: On HTTP 404.
            RWSHTTPError: On any other HTTP >= 400.
            RWSConnectionError: If the controller is unreachable.
            RWSTimeoutError: If the request exceeds the timeout.

        Example:
            ```python
            >>> resp = client.options("ctrl/network/route/add")
            ```
        """
        return self._request("OPTIONS", path, **kwargs)
