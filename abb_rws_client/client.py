# abb_rws_client/client.py
"""
Session HTTP vers un contrôleur ABB RWS (RobotWare 6).

Responsabilités de ce module :
- Créer et maintenir un httpx.AsyncClient configuré pour RWS
- Gérer l'authentification HTTP Digest ABB
- Maintenir le cookie de session ABBCX
- Exposer les méthodes HTTP de bas niveau (get, put, post)
  utilisées par les modules de haut niveau (mastership, rapid_variable, execution)
- Implémenter la politique de retry sur erreurs transport

Ce module ne contient PAS de logique métier RAPID — il est purement
responsable de la couche transport HTTP.

Politique de retry (documentée ici, implémentée dans _request) :
    - Déclencheurs : ConnectError, ReadTimeout, PoolTimeout uniquement
      Raison : ces erreurs sont des aléas réseau transitoires, pas des
      réponses logiques du contrôleur. Les erreurs HTTP (4xx, 5xx) ne
      sont jamais retentées car elles représentent une réponse valide
      et intentionnelle du contrôleur.
    - Tentatives : 3 au total (1 essai initial + 2 retries)
      Raison : au-delà de 3 tentatives, un échec réseau est probablement
      structurel (câble débranché, contrôleur éteint) et doit remonter.
    - Délai : exponentiel avec jitter ±10%
      base * 2^attempt + jitter  →  ~0.5s, ~1s, ~2s
      Raison : l'exponentiel évite de saturer un contrôleur en cours de
      redémarrage ; le jitter évite les "thundering herds" si plusieurs
      clients se reconnectent simultanément.
    - Jamais sur 401 : un échec d'authentification Digest persistant
      indique des credentials incorrects, pas un aléa réseau.

Gestion du cookie ABBCX (documentée ici) :
    Le contrôleur ABB envoie un cookie ABBCX après le premier handshake
    Digest réussi. httpx.AsyncClient maintient ce cookie nativement via
    son cookiejar interne pour toute la durée de vie du client.
    En cas d'expiration de session (timeout d'inactivité ABB ~10 min),
    le contrôleur répond 401 et httpx.DigestAuth relance automatiquement
    le handshake — le cookie est alors renouvelé de façon transparente.
    Aucune logique de renouvellement explicite n'est donc nécessaire.
"""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType
from typing import Self

import httpx

from abb_rws_client.exceptions import (
    RWSAuthenticationError,
    RWSConnectionError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de retry
# Toutes les valeurs sont ici, jamais en dur dans le code, pour faciliter
# les tests et la compréhension de la politique.
# ---------------------------------------------------------------------------

#: Nombre total de tentatives (1 essai initial + RETRY_MAX_ATTEMPTS - 1 retries)
_RETRY_MAX_ATTEMPTS: int = 3

#: Délai de base en secondes pour le calcul exponentiel
#: Délai effectif : _RETRY_BASE_DELAY * 2^attempt  →  0.5s, 1.0s, 2.0s
_RETRY_BASE_DELAY: float = 0.5

#: Amplitude du jitter aléatoire appliqué au délai (fraction du délai calculé)
#: Exemple : jitter=0.1 → ±10% du délai  →  évite les reconnexions synchronisées
_RETRY_JITTER: float = 0.1

#: Types d'exceptions httpx déclenchant un retry
#: Seules les erreurs transport sont retentées — jamais les erreurs HTTP
_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.PoolTimeout,
)


# ---------------------------------------------------------------------------
# RWSClient
# ---------------------------------------------------------------------------


class RWSClient:
    """Client HTTP async pour l'API Robot Web Services (RWS) d'ABB RobotWare 6.

    Ce client est conçu pour être utilisé comme context manager async,
    ce qui garantit la fermeture propre de la session HTTP dans tous les
    cas (succès, exception, interruption).

    La durée de vie du context manager est illimitée : il peut rester
    ouvert pendant des heures pour des applications de type watchdog ou
    supervision continue. Le mastership RAPID, lui, doit être acquis et
    libéré de façon chirurgicale via son propre context manager imbriqué
    (voir mastership.py).

    Example:
        Utilisation recommandée (context manager) ::

            async with RWSClient(host="192.168.125.1") as client:
                state = await client.get("/rw/rapid/execution", params={"json": "1"})

        Utilisation avancée (gestion manuelle) ::

            client = RWSClient(host="192.168.125.1")
            await client.aopen()
            try:
                ...
            finally:
                await client.aclose()

    Args:
        host: Adresse IP ou hostname du contrôleur ABB, sans slash final.
              Exemple : "192.168.125.1"
        username: Nom d'utilisateur RWS. Défaut ABB RW6 : "Default User".
        password: Mot de passe RWS. Défaut ABB RW6 : "robotics".
        timeout: Timeout HTTP global en secondes, appliqué à chaque requête
                 individuelle (connect + read). Défaut : 10.0s.
        verify_ssl: Vérification du certificat SSL. False par défaut car
                    les contrôleurs ABB utilisent HTTP (pas HTTPS) en RW6.

    Attributes:
        base_url: URL de base construite à partir de host.
                  Toujours de la forme "http://<host>/".
    """

    def __init__(
        self,
        host: str,
        username: str = "Default User",
        password: str = "robotics",
        timeout: float = 10.0,
        verify_ssl: bool = False,
    ) -> None:
        # URL de base : httpx attend un trailing slash pour la résolution relative
        self.base_url: str = f"http://{host}/"

        # Stockage des paramètres de connexion pour documentation et réouverture
        self._host = host
        self._username = username
        self._timeout = timeout
        self._verify_ssl = verify_ssl

        # Auth Digest ABB
        # httpx.DigestAuth gère le challenge/response automatiquement :
        # 1. Première requête envoyée sans credentials
        # 2. Contrôleur répond 401 avec WWW-Authenticate: Digest ...
        # 3. httpx calcule la réponse Digest et renvoie la requête
        # 4. Cookie ABBCX reçu et stocké dans le cookiejar du client
        self._auth = httpx.DigestAuth(username=username, password=password)

        # Le client httpx est créé dans aopen() / __aenter__()
        # Il est None tant que le client n'est pas ouvert.
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Context manager async
    # ------------------------------------------------------------------

    async def __aenter__(self) -> Self:
        """Ouvre la session HTTP et retourne le client prêt à l'emploi."""
        await self.aopen()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Ferme la session HTTP proprement, même en cas d'exception."""
        await self.aclose()

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    async def aopen(self) -> None:
        """Ouvre la session HTTP.

        Crée le httpx.AsyncClient avec la configuration RWS :
        - Auth Digest
        - Cookie jar partagé (maintien du cookie ABBCX)
        - Timeout global
        - Headers par défaut attendus par RWS

        Cette méthode est idempotente : si le client est déjà ouvert,
        elle ne fait rien.
        """
        if self._http is not None:
            # Déjà ouvert — idempotent, pas d'erreur
            logger.debug("RWSClient.aopen() called but client is already open — no-op")
            return

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self._auth,
            timeout=httpx.Timeout(self._timeout),
            verify=self._verify_ssl,
            # Headers par défaut pour RWS :
            # - Accept: application/json → on veut du JSON, pas du XML
            # - User-Agent : identifie le client dans les logs ABB
            headers={
                "Accept": "application/json",
                "User-Agent": "abb-rws6-python-client/0.1.0",
            },
            # follow_redirects : certains endpoints RWS retournent 302
            follow_redirects=True,
        )
        logger.debug("RWSClient opened — base_url=%s, user=%s", self.base_url, self._username)

    async def aclose(self) -> None:
        """Ferme la session HTTP et libère les ressources.

        Après appel, le client ne peut plus être utilisé sans appeler
        aopen() à nouveau. Cette méthode est idempotente.
        """
        if self._http is None:
            logger.debug("RWSClient.aclose() called but client is already closed — no-op")
            return
        await self._http.aclose()
        self._http = None
        logger.debug("RWSClient closed — host=%s", self._host)

    # ------------------------------------------------------------------
    # Méthodes HTTP de bas niveau
    # ------------------------------------------------------------------

    async def get(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Envoie une requête GET vers un endpoint RWS.

        Args:
            path: Chemin relatif à la base URL, sans slash initial.
                  Exemple : "rw/rapid/execution"
            params: Paramètres de query string.
                    Exemple : {"json": "1"}

        Returns:
            La réponse httpx après validation du status code.

        Raises:
            RWSConnectionError: Impossible de joindre le contrôleur.
            RWSTimeoutError: Le contrôleur n'a pas répondu dans le délai.
            RWSAuthenticationError: Credentials Digest invalides.
            RWSNotFoundError: Ressource introuvable (404).
            RWSHTTPError: Toute autre réponse HTTP >= 400.
        """
        return await self._request("GET", path, params=params)

    async def put(
        self,
        path: str,
        data: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Envoie une requête PUT vers un endpoint RWS.

        Utilisé pour l'écriture de variables RAPID.
        Le body est encodé en application/x-www-form-urlencoded,
        conformément à la spécification RWS ABB.

        Args:
            path: Chemin relatif à la base URL.
            data: Données du body sous forme de dict clé/valeur.
                  Exemple : {"value": "42"}
            params: Paramètres de query string optionnels.

        Returns:
            La réponse httpx après validation du status code.

        Raises:
            Mêmes exceptions que get().
        """
        return await self._request("PUT", path, data=data, params=params)

    async def post(
        self,
        path: str,
        data: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Envoie une requête POST vers un endpoint RWS.

        Utilisé pour les actions RWS : acquisition/libération du mastership,
        démarrage/arrêt de l'exécution RAPID, etc.

        Args:
            path: Chemin relatif à la base URL.
            data: Données du body sous forme de dict clé/valeur.
            params: Paramètres de query string optionnels.

        Returns:
            La réponse httpx après validation du status code.

        Raises:
            Mêmes exceptions que get().
        """
        return await self._request("POST", path, data=data, params=params)

    # ------------------------------------------------------------------
    # Moteur de requête avec retry
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Moteur interne de requête HTTP avec retry sur erreurs transport.

        C'est ici que sont centralisées :
        - La vérification que le client est ouvert
        - La politique de retry (voir module docstring pour la justification)
        - La traduction des exceptions httpx → exceptions RWS custom
        - La validation des status codes HTTP

        Args:
            method: Verbe HTTP : "GET", "PUT", "POST".
            path: Chemin relatif à la base URL.
            data: Body encodé en form-urlencoded (pour PUT/POST).
            params: Query string parameters.

        Returns:
            httpx.Response avec status code validé (< 400).

        Raises:
            RuntimeError: Si le client n'est pas ouvert (aopen() non appelé).
            RWSConnectionError: Après épuisement des retries sur ConnectError.
            RWSTimeoutError: Après épuisement des retries sur ReadTimeout/PoolTimeout.
            RWSAuthenticationError: Sur réponse 401.
            RWSNotFoundError: Sur réponse 404.
            RWSHTTPError: Sur toute autre réponse >= 400.
        """
        if self._http is None:
            raise RuntimeError(
                "RWSClient is not open. Use 'async with RWSClient(...) as client' "
                "or call await client.aopen() before making requests."
            )

        last_exception: Exception | None = None

        for attempt in range(_RETRY_MAX_ATTEMPTS):
            if attempt > 0:
                # Calcul du délai exponentiel avec jitter
                # Formule : base * 2^(attempt-1) * (1 ± jitter)
                # attempt=1 → ~0.5s, attempt=2 → ~1.0s
                raw_delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                jitter = raw_delay * _RETRY_JITTER * (2 * random.random() - 1)
                delay = raw_delay + jitter
                logger.warning(
                    "RWS %s %s — retry %d/%d in %.2fs (reason: %s)",
                    method,
                    path,
                    attempt,
                    _RETRY_MAX_ATTEMPTS - 1,
                    delay,
                    type(last_exception).__name__,
                )
                await asyncio.sleep(delay)

            try:
                response = await self._http.request(
                    method=method,
                    url=path,
                    data=data,
                    params=params,
                )
            except _RETRYABLE_EXCEPTIONS as exc:
                # Erreur transport retentable — on boucle
                last_exception = exc
                continue
            except httpx.ConnectTimeout as exc:
                # ConnectTimeout est distinct de ReadTimeout dans httpx
                # et mérite aussi un retry
                last_exception = exc
                continue
            except httpx.HTTPError as exc: # pragma: no cover
                # Toute autre erreur httpx non retentable (ex: InvalidURL)
                # On lève immédiatement sans retry
                raise RWSConnectionError(
                    f"HTTP error on {method} {path}: {exc}"
                ) from exc

            # Requête réussie au niveau transport — on sort de la boucle retry
            logger.debug(
                "RWS %s %s → %d (attempt %d)",
                method,
                path,
                response.status_code,
                attempt + 1,
            )
            return self._raise_for_status(response, method, path)

        # Tous les retries épuisés — on lève l'exception appropriée
        assert last_exception is not None  # garanti par la logique ci-dessus
        if isinstance(last_exception, (httpx.ReadTimeout, httpx.PoolTimeout)):
            raise RWSTimeoutError(
                f"Timeout after {_RETRY_MAX_ATTEMPTS} attempts on {method} {path} "
                f"(timeout={self._timeout}s)"
            ) from last_exception
        raise RWSConnectionError(
            f"Connection failed after {_RETRY_MAX_ATTEMPTS} attempts on {method} {path}"
        ) from last_exception

    # ------------------------------------------------------------------
    # Validation des status codes
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(
        response: httpx.Response,
        method: str,
        path: str,
    ) -> httpx.Response:
        """Valide le status code HTTP et lève l'exception RWS appropriée.

        Mapping status → exception :
            401 → RWSAuthenticationError  (credentials Digest invalides)
            404 → RWSNotFoundError        (ressource / variable inexistante)
            4xx → RWSHTTPError            (erreur client générique)
            5xx → RWSHTTPError            (erreur serveur contrôleur)
            2xx → retourne la réponse     (succès)
            3xx → ne devrait pas arriver  (follow_redirects=True)

        Note sur les codes 2xx de RWS :
            RWS utilise parfois 204 No Content pour les actions (POST mastership).
            Ces codes sont valides et retournés sans erreur.

        Args:
            response: Réponse httpx à valider.
            method: Verbe HTTP (pour le message d'erreur).
            path: Chemin (pour le message d'erreur).

        Returns:
            La réponse inchangée si le status est acceptable.

        Raises:
            RWSAuthenticationError: Sur 401.
            RWSNotFoundError: Sur 404.
            RWSHTTPError: Sur tout autre status >= 400.
        """
        if response.status_code == 401:
            raise RWSAuthenticationError(
                f"Authentication failed on {method} {path} — "
                f"check credentials (user='{response.request.headers.get('authorization', 'N/A')}')"
            )
        if response.status_code == 404:
            raise RWSNotFoundError(resource=path)
        if response.status_code >= 400:
            raise RWSHTTPError(
                f"HTTP {response.status_code} on {method} {path}: {response.text[:200]}",
                status_code=response.status_code,
            )
        return response

    # ------------------------------------------------------------------
    # Représentation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "open" if self._http is not None else "closed"
        return (
            f"RWSClient("
            f"host={self._host!r}, "
            f"user={self._username!r}, "
            f"timeout={self._timeout}, "
            f"status={status!r})"
        )
