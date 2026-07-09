# abb_rws_client/rws/rapid/execution.py
"""
Miroir 1:1 du RAPID Execution Service RWS ABB RobotWare 6.

Routes couvertes :
    GET  /rw/rapid/execution              → état d'exécution complet
    POST /rw/rapid/execution/start        → démarrer l'exécution RAPID
    POST /rw/rapid/execution/stop         → arrêter l'exécution RAPID
    POST /rw/rapid/execution/resetpp      → reset du program pointer vers main

Référence : ABB RobotWare 6 — Robot Web Services API — RAPID Service

Contraintes ABB :
    - start/stop/resetpp nécessitent le mastership (acquis via mastership.py).
    - start accepte les paramètres optionnels : regain, execmode, cycle,
      condition, stopatbp, alltaskbytsp (passés en form-data).
    - stop accepte le paramètre optionnel : stopmode (instr|cycle|task).
    - L'état retourné par get_execution_state est une string parmi :
      "running", "stopped", "stopped_at_breakpoint", "initializing".

Status  : tested
Coverage: 100%
"""

from __future__ import annotations

import httpx

from abb_rws_client._core.client import RWSClient

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_EXECUTION_PATH = "rw/rapid/execution"
_EXECUTION_START_PATH = "rw/rapid/execution/start"
_EXECUTION_STOP_PATH = "rw/rapid/execution/stop"
_EXECUTION_RESETPP_PATH = "rw/rapid/execution/resetpp"


async def get_execution_state(client: RWSClient) -> httpx.Response:
    """Retourne l'état courant d'exécution RAPID.

    Route : GET /rw/rapid/execution

    Contraintes ABB :
        - Accessible sans mastership (lecture seule).
        - La réponse XML/JSON contient le champ ``ctrlexecstate`` avec les
          valeurs possibles : ``"running"``, ``"stopped"``,
          ``"stopped_at_breakpoint"``, ``"initializing"``.
        - Paramètre ``?json=1`` recommandé pour obtenir du JSON.

    Args:
        client: Instance RWSClient ouverte et authentifiée.

    Returns:
        Réponse httpx brute. Le corps contient l'état d'exécution RAPID.

    Raises:
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSHTTPError: Sur toute autre erreur HTTP >= 400.
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     resp = await get_execution_state(client)
        ...     print(resp.status_code)  # 200
    """
    return await client.get(_EXECUTION_PATH, params={"json": "1"})


async def start_execution(
    client: RWSClient,
    *,
    regain: str = "continue",
    execmode: str = "continue",
    cycle: str = "forever",
    condition: str = "none",
    stopatbp: str = "disabled",
    alltaskbytsp: str = "false",
) -> httpx.Response:
    """Démarre l'exécution RAPID.

    Route : POST /rw/rapid/execution/start

    Contraintes ABB :
        - Nécessite le mastership RAPID (acquis via mastership_request).
        - Le contrôleur doit être en mode AUTO ou MANUAL avec moteurs ON.
        - Lève RWSHTTPError (HTTP 409) si l'exécution est déjà en cours.

    Args:
        client: Instance RWSClient ouverte et authentifiée.
        regain: Comportement de reprise. Valeurs : ``"continue"``,
            ``"regain"``, ``"clear"``, ``"enterrecovery"``. Défaut : ``"continue"``.
        execmode: Mode d'exécution. Valeurs : ``"continue"``, ``"stepin"``,
            ``"stepover"``, ``"stepout"``, ``"stepback"``, ``"steplast"``,
            ``"stepmotion"``. Défaut : ``"continue"``.
        cycle: Nombre de cycles. Valeurs : ``"forever"``, ``"asis"``,
            ``"once"``. Défaut : ``"forever"``.
        condition: Condition de démarrage. Valeurs : ``"none"``,
            ``"callchain"``. Défaut : ``"none"``.
        stopatbp: Arrêt sur breakpoint. Valeurs : ``"enabled"``,
            ``"disabled"``. Défaut : ``"disabled"``.
        alltaskbytsp: Démarrage de toutes les tâches. Valeurs : ``"true"``,
            ``"false"``. Défaut : ``"false"``.

    Returns:
        Réponse httpx brute (HTTP 204 No Content en cas de succès).

    Raises:
        RWSHTTPError: Si l'exécution est déjà en cours (HTTP 409) ou autre
            erreur HTTP >= 400.
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     await mastership_request(client)
        ...     await start_execution(client, cycle="once")
    """
    return await client.post(
        _EXECUTION_START_PATH,
        data={
            "regain": regain,
            "execmode": execmode,
            "cycle": cycle,
            "condition": condition,
            "stopatbp": stopatbp,
            "alltaskbytsp": alltaskbytsp,
        },
    )


async def stop_execution(
    client: RWSClient,
    *,
    stopmode: str = "cycle",
) -> httpx.Response:
    """Arrête l'exécution RAPID.

    Route : POST /rw/rapid/execution/stop

    Contraintes ABB :
        - Nécessite le mastership RAPID.
        - Lève RWSHTTPError (HTTP 409) si l'exécution est déjà arrêtée.

    Args:
        client: Instance RWSClient ouverte et authentifiée.
        stopmode: Mode d'arrêt. Valeurs : ``"cycle"`` (fin du cycle en
            cours), ``"instr"`` (fin de l'instruction en cours),
            ``"task"`` (fin de la tâche). Défaut : ``"cycle"``.

    Returns:
        Réponse httpx brute (HTTP 204 No Content en cas de succès).

    Raises:
        RWSHTTPError: Si l'exécution est déjà arrêtée (HTTP 409).
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     await stop_execution(client, stopmode="instr")
    """
    return await client.post(
        _EXECUTION_STOP_PATH,
        data={"stopmode": stopmode},
    )


async def reset_program_pointer(client: RWSClient) -> httpx.Response:
    """Remet le program pointer RAPID au début du main.

    Route : POST /rw/rapid/execution/resetpp

    Contraintes ABB :
        - Nécessite le mastership RAPID.
        - L'exécution doit être arrêtée avant d'appeler cette fonction.
        - Lève RWSHTTPError (HTTP 409) si l'exécution est en cours.

    Args:
        client: Instance RWSClient ouverte et authentifiée.

    Returns:
        Réponse httpx brute (HTTP 204 No Content en cas de succès).

    Raises:
        RWSHTTPError: Si l'exécution est en cours (HTTP 409).
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     await reset_program_pointer(client)
    """
    return await client.post(_EXECUTION_RESETPP_PATH)
