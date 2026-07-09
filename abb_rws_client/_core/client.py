# abb_rws_client/_core/client.py
"""
Session HTTP vers un contrôleur ABB RWS (RobotWare 6).

Responsabilités de ce module :
- Créer et maintenir un httpx.AsyncClient configuré pour RWS
- Gérer l'authentification HTTP Digest ABB
- Maintenir le cookie de session ABBCX
- Exposer les méthodes HTTP de bas niveau (get, put, post)
  utilisées par les modules rws/ et highlevel/
- Implémenter la politique de retry sur erreurs transport
- Fournir RWSClientSync, wrapper synchrone sans duplication de logique

Politique de retry (documentée ici, implémentée dans _request) :
    - Déclencheurs : ConnectError, ReadTimeout, PoolTimeout uniquement.
      Les erreurs HTTP (4xx, 5xx) ne sont jamais retentées.
    - Tentatives : 3 au total (1 essai initial + 2 retries)
    - Délai : exponentiel avec jitter ±10%
      base * 2^attempt + jitter  →  ~0.5s, ~1s, ~2s

Gestion du cookie ABBCX :
    httpx.AsyncClient maintient ce cookie nativement via son cookiejar.
    En cas d'expiration (timeout ABB ~10 min), le contrôleur répond 401
    et httpx.DigestAuth relance le handshake automatiquement.

RWSClientSync :
    Wrapper synchrone basé sur httpx.Client (sync natif d'httpx).
    Même logique de retry/auth, aucune dépendance anyio au runtime.
    Toutes les méthodes sont synchrones (pas de async def).
"""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType
from typing import Any, Self

import httpx

from abb_rws_client._core.exceptions import (
    RWSAuthenticationError,
    RWSConnectionError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de retry
# ---------------------------------------------------------------------------

#: Nombre total de tentatives (1 essai initial + _RETRY_MAX_ATTEMPTS - 1 retries)
_RETRY_MAX_ATTEMPTS: int = 3

#: Délai de base en secondes : _RETRY_BASE_DELAY * 2^attempt → 0.5s, 1.0s, 2.0s
_RETRY_BASE_DELAY: float = 0.5

#: Amplitude du jitter (fraction du délai calculé) → ±10%
_RETRY_JITTER: float = 0.1

#: Types d'exceptions httpx déclenchant un retry (erreurs transport uniquement)
_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.PoolTimeout,
)

# ---------------------------------------------------------------------------
# Helpers partagés async/sync
# ---------------------------------------------------------------------------


def _build_auth(username: str, password: str) -> httpx.DigestAuth:
    """Construit l'objet DigestAuth httpx."""
    return httpx.DigestAuth(username, password)


def _raise_for_status(response: httpx.Response, path: str) -> None:
    """Lève l'exception RWS appropriée selon le status HTTP.

    Args:
        response: Réponse httpx reçue.
        path: Chemin de la requête, pour les messages d'erreur.

    Raises:
        RWSAuthenticationError: Sur HTTP 401.
        RWSNotFoundError: Sur HTTP 404.
        RWSHTTPError: Sur tout autre status >= 400.
    """
    code = response.status_code
    if code == 401:
        raise RWSAuthenticationError()
    if code == 404:
        raise RWSNotFoundError(path)
    if code >= 400:
        raise RWSHTTPError(
            f"HTTP {code} on {path}: {response.text[:200]}",
            status_code=code,
        )


def _retry_delay(attempt: int) -> float:
    """Calcule le délai avant le prochain retry avec jitter.

    Args:
        attempt: Numéro de la tentative échouée (0-indexé).

    Returns:
        Délai en secondes (float).
    """
    base = _RETRY_BASE_DELAY * (2**attempt)
    jitter = base * _RETRY_JITTER * (2 * random.random() - 1)
    return base + jitter


# ---------------------------------------------------------------------------
# RWSClient — async
# ---------------------------------------------------------------------------


class RWSClient:
    """Client HTTP async pour l'API Robot Web Services (RWS) d'ABB RobotWare 6.

    Conçu pour être utilisé comme context manager async, ce qui garantit
    la fermeture propre de la session HTTP dans tous les cas.

    Args:
        host: Adresse IP ou hostname du contrôleur (ex: ``"192.168.125.1"``).
        username: Identifiant RWS (défaut ABB : ``"Default User"``).
        password: Mot de passe RWS (défaut ABB : ``"robotics"``).
        port: Port HTTP du contrôleur (défaut : ``80``).
        timeout: Timeout HTTP en secondes (défaut : ``10.0``).

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     resp = await client.get("rw/rapid/execution")
    """

    def __init__(
        self,
        host: str,
        username: str = "Default User",
        password: str = "robotics",
        port: int = 80,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/"
        self._http: httpx.AsyncClient | None = None

    # ── Cycle de vie ────────────────────────────────────────────────────────

    async def aopen(self) -> None:
        """Ouvre la session HTTP. Idempotent : sans effet si déjà ouvert.

        Raises:
            RWSConnectionError: Si la connexion initiale échoue.
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
        """Ferme la session HTTP. Idempotent : sans effet si déjà fermé."""
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

    # ── Requête interne avec retry ───────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Exécute une requête HTTP avec politique de retry sur erreurs transport.

        Args:
            method: Méthode HTTP (``"GET"``, ``"POST"``, ``"PUT"``, ``"DELETE"``).
            path: Chemin relatif à la base URL (ex: ``"rw/rapid/execution"``).
            **kwargs: Paramètres supplémentaires passés à httpx (params, data, json…).

        Returns:
            Réponse httpx (status non vérifié — appeler ``_raise_for_status`` si besoin).

        Raises:
            RuntimeError: Si le client n'est pas ouvert.
            RWSConnectionError: Après épuisement des retries sur ConnectError.
            RWSTimeoutError: Après épuisement des retries sur ReadTimeout/PoolTimeout.
            RWSAuthenticationError: Sur HTTP 401.
            RWSNotFoundError: Sur HTTP 404.
            RWSHTTPError: Sur tout autre HTTP >= 400.
        """
        if self._http is None:
            raise RuntimeError(
                "RWSClient is not open. Use 'async with RWSClient(...) as client' "
                "or call await client.aopen() first."
            )
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
        # Tous les retries épuisés
        assert last_exc is not None
        if isinstance(last_exc, httpx.ConnectError):
            raise RWSConnectionError(
                f"Connection failed to {self.base_url}: {last_exc}"
            ) from last_exc
        raise RWSTimeoutError(
            f"Timeout on {method} {path} after {_RETRY_MAX_ATTEMPTS} attempts"
        ) from last_exc

    # ── Méthodes HTTP publiques ──────────────────────────────────────────────

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Effectue un GET RWS.

        Route : toute route GET de l'API RWS.

        Args:
            path: Chemin relatif (ex: ``"rw/rapid/execution"``).
            **kwargs: Paramètres httpx (``params``, ``headers``…).

        Returns:
            Réponse httpx validée (status < 400).

        Raises:
            RWSConnectionError: Erreur réseau après retries.
            RWSTimeoutError: Timeout après retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Autre HTTP >= 400.

        Example:
            >>> resp = await client.get("rw/rapid/execution", params={"json": "1"})
        """
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Effectue un POST RWS.

        Route : toute route POST de l'API RWS (actions, mastership…).

        Args:
            path: Chemin relatif (ex: ``"rw/mastership"``).
            **kwargs: Paramètres httpx (``params``, ``data``, ``json``…).

        Returns:
            Réponse httpx validée (status < 400).

        Raises:
            RWSConnectionError: Erreur réseau après retries.
            RWSTimeoutError: Timeout après retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Autre HTTP >= 400.

        Example:
            >>> await client.post("rw/mastership", params={"action": "request"})
        """
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Effectue un PUT RWS.

        Route : typiquement PUT /rw/rapid/symbol/data/... pour écrire une variable.

        Args:
            path: Chemin relatif.
            **kwargs: Paramètres httpx (``data``…).

        Returns:
            Réponse httpx validée (status < 400).

        Raises:
            RWSConnectionError: Erreur réseau après retries.
            RWSTimeoutError: Timeout après retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Autre HTTP >= 400.

        Example:
            >>> await client.put(
            ...     "rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR",
            ...     data={"value": "42"},
            ... )
        """
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Effectue un DELETE RWS.

        Route : typiquement DELETE /fileservice/... ou DELETE /rw/elog/...

        Args:
            path: Chemin relatif.
            **kwargs: Paramètres httpx.

        Returns:
            Réponse httpx validée (status < 400).

        Raises:
            RWSConnectionError: Erreur réseau après retries.
            RWSTimeoutError: Timeout après retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Autre HTTP >= 400.
        """
        return await self._request("DELETE", path, **kwargs)

    async def head(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Envoie une requête HTTP HEAD.

        Route: ``HEAD {path}``

        Args:
            path: Chemin relatif à la base URL du contrôleur.
            **kwargs: Paramètres supplémentaires passés à httpx.

        Returns:
            Réponse HTTP brute.

        Raises:
            RWSAuthenticationError: Sur HTTP 401.
            RWSNotFoundError: Sur HTTP 404.
            RWSHTTPError: Sur tout autre HTTP >= 400.
            RWSConnectionError: Si le contrôleur est injoignable.
            RWSTimeoutError: Si la requête dépasse le timeout.

        Example:
            >>> resp = await client.head("fileservice/$HOME/myfile.txt")
        """
        return await self._request("HEAD", path, **kwargs)

    async def options(
        self,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Envoie une requête HTTP OPTIONS.

        Route: ``OPTIONS {path}``

        Args:
            path: Chemin relatif à la base URL du contrôleur.
            **kwargs: Paramètres supplémentaires passés à httpx.

        Returns:
            Réponse HTTP brute.

        Raises:
            RWSAuthenticationError: Sur HTTP 401.
            RWSNotFoundError: Sur HTTP 404.
            RWSHTTPError: Sur tout autre HTTP >= 400.
            RWSConnectionError: Si le contrôleur est injoignable.
            RWSTimeoutError: Si la requête dépasse le timeout.

        Example:
            >>> resp = await client.options("ctrl/network/route/add")
        """
        return await self._request("OPTIONS", path, **kwargs)

# ---------------------------------------------------------------------------
# RWSClientSync — wrapper synchrone
# ---------------------------------------------------------------------------


class RWSClientSync:
    """Client HTTP synchrone pour l'API RWS ABB RobotWare 6.

    Wrapper synchrone de ``RWSClient`` basé sur ``httpx.Client`` natif.
    Même politique d'auth (DigestAuth), même retry, même gestion d'erreurs.
    Aucune dépendance ``anyio`` ou ``asyncio`` au runtime.

    Conçu pour être utilisé comme context manager synchrone.

    Args:
        host: Adresse IP ou hostname du contrôleur.
        username: Identifiant RWS (défaut ABB : ``"Default User"``).
        password: Mot de passe RWS (défaut ABB : ``"robotics"``).
        port: Port HTTP (défaut : ``80``).
        timeout: Timeout HTTP en secondes (défaut : ``10.0``).

    Example:
        >>> with RWSClientSync(host="192.168.125.1") as client:
        ...     resp = client.get("rw/rapid/execution")
    """

    def __init__(
        self,
        host: str,
        username: str = "Default User",
        password: str = "robotics",
        port: int = 80,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/"
        self._http: httpx.Client | None = None

    # ── Cycle de vie ────────────────────────────────────────────────────────

    def open(self) -> None:
        """Ouvre la session HTTP. Idempotent : sans effet si déjà ouvert."""
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
        """Ferme la session HTTP. Idempotent : sans effet si déjà fermé."""
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

    # ── Requête interne avec retry ───────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Exécute une requête HTTP synchrone avec politique de retry.

        Args:
            method: Méthode HTTP.
            path: Chemin relatif.
            **kwargs: Paramètres httpx.

        Returns:
            Réponse httpx validée.

        Raises:
            RuntimeError: Si le client n'est pas ouvert.
            RWSConnectionError: Après épuisement des retries.
            RWSTimeoutError: Après épuisement des retries.
            RWSAuthenticationError: HTTP 401.
            RWSNotFoundError: HTTP 404.
            RWSHTTPError: Autre HTTP >= 400.
        """
        if self._http is None:
            raise RuntimeError(
                "RWSClientSync is not open. Use 'with RWSClientSync(...) as client' "
                "or call client.open() first."
            )
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
        assert last_exc is not None
        if isinstance(last_exc, httpx.ConnectError):
            raise RWSConnectionError(f"Cannot connect to {self.base_url}: {last_exc}") from last_exc
        raise RWSTimeoutError(
            f"Timeout on {method} {path} after {_RETRY_MAX_ATTEMPTS} attempts"
        ) from last_exc

    # ── Méthodes HTTP publiques ──────────────────────────────────────────────

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """GET synchrone RWS.

        Args:
            path: Chemin relatif (ex: ``"rw/rapid/execution"``).
            **kwargs: Paramètres httpx (``params``…).

        Returns:
            Réponse httpx validée.

        Example:
            >>> resp = client.get("rw/rapid/execution", params={"json": "1"})
        """
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """POST synchrone RWS.

        Args:
            path: Chemin relatif.
            **kwargs: Paramètres httpx (``params``, ``data``…).

        Returns:
            Réponse httpx validée.
        """
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """PUT synchrone RWS.

        Args:
            path: Chemin relatif.
            **kwargs: Paramètres httpx (``data``…).

        Returns:
            Réponse httpx validée.
        """
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """DELETE synchrone RWS.

        Args:
            path: Chemin relatif.
            **kwargs: Paramètres httpx.

        Returns:
            Réponse httpx validée.
        """
        return self._request("DELETE", path, **kwargs)
        
    def head(self, path: str, **kwargs: Any) -> httpx.Response:
        """Envoie une requête HTTP HEAD (synchrone).

        Args:
            path: Chemin relatif à la base URL.
            **kwargs: Paramètres supplémentaires passés à httpx.

        Returns:
            Réponse HTTP brute.

        Raises:
            RWSAuthenticationError: Sur HTTP 401.
            RWSNotFoundError: Sur HTTP 404.
            RWSHTTPError: Sur tout autre HTTP >= 400.
        """
        return self._request("HEAD", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> httpx.Response:
        """Envoie une requête HTTP OPTIONS (synchrone).

        Args:
            path: Chemin relatif à la base URL.
            **kwargs: Paramètres supplémentaires passés à httpx.

        Returns:
            Réponse HTTP brute.

        Raises:
            RWSAuthenticationError: Sur HTTP 401.
            RWSNotFoundError: Sur HTTP 404.
            RWSHTTPError: Sur tout autre HTTP >= 400.
        """
        return self._request("OPTIONS", path, **kwargs)
