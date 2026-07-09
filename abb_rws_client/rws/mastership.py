# abb_rws_client/rws/mastership.py
"""
Miroir 1:1 du Mastership Service RWS ABB RobotWare 6.

Routes couvertes :
    POST /rw/mastership/request  → acquérir le mastership global
    POST /rw/mastership/release  → libérer le mastership global

Référence : ABB RobotWare 6 — Robot Web Services API — Mastership Service

Contraintes ABB :
    - Le mastership doit être acquis avant toute écriture de variable RAPID.
    - Un seul client peut détenir le mastership à la fois.
    - En cas de déconnexion, le contrôleur libère automatiquement le mastership
      après un timeout (~10 s).
    - Le mastership global couvre RAPID et Motion simultanément.

Status  : tested
Coverage: 100%
"""

from __future__ import annotations

import httpx

from abb_rws_client._core.client import RWSClient

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_MASTERSHIP_REQUEST_PATH = "rw/mastership/request"
_MASTERSHIP_RELEASE_PATH = "rw/mastership/release"


async def mastership_request(client: RWSClient) -> httpx.Response:
    """Acquiert le mastership global sur le contrôleur ABB.

    Route : POST /rw/mastership/request

    Contraintes ABB :
        - Doit être appelé avant toute écriture de variable RAPID ou motion.
        - Lève RWSHTTPError (HTTP 409) si le mastership est déjà détenu
          par un autre client.
        - Lève RWSAuthenticationError (HTTP 401) si la session a expiré.

    Args:
        client: Instance RWSClient ouverte et authentifiée.

    Returns:
        Réponse httpx brute (HTTP 204 No Content en cas de succès).

    Raises:
        RWSHTTPError: Si le mastership est déjà détenu (HTTP 409) ou autre
            erreur HTTP >= 400.
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     await mastership_request(client)
    """
    return await client.post(_MASTERSHIP_REQUEST_PATH)


async def mastership_release(client: RWSClient) -> httpx.Response:
    """Libère le mastership global sur le contrôleur ABB.

    Route : POST /rw/mastership/release

    Contraintes ABB :
        - Doit être appelé après toute séquence d'écriture pour libérer
          les autres clients.
        - Lève RWSHTTPError (HTTP 409) si le mastership n'est pas détenu
          par ce client.
        - Sans effet si le mastership a déjà été libéré automatiquement
          par timeout.

    Args:
        client: Instance RWSClient ouverte et authentifiée.

    Returns:
        Réponse httpx brute (HTTP 204 No Content en cas de succès).

    Raises:
        RWSHTTPError: Si ce client ne détient pas le mastership (HTTP 409).
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     await mastership_release(client)
    """
    return await client.post(_MASTERSHIP_RELEASE_PATH)
