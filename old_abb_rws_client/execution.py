# abb_rws_client/execution.py
"""
Contrôle de l'exécution RAPID sur un contrôleur ABB RobotWare 6.

Ce module expose une API 1:1 avec les endpoints RWS de la branche
/rw/rapid/execution (cf. arbre RWS : /rw → /rapid → /execution).

Routes couvertes :
    GET  /rw/rapid/execution              → état d'exécution complet
    POST /rw/rapid/execution/start        → démarrer l'exécution RAPID
    POST /rw/rapid/execution/stop         → arrêter l'exécution RAPID
    POST /rw/rapid/execution/resetpp      → reset du program pointer vers main

Valeurs retournées par le contrôleur (champ "ctrlexecstate") :
    "running"  → programme RAPID en cours d'exécution
    "stopped"  → programme arrêté (après stop ou fin de cycle)

Contraintes ABB RW6 :
    - resetpp  : nécessite le mastership RAPID (appelant responsable)
    - start    : NE doit PAS être appelé avec le mastership actif
                 → utiliser le paramètre mastership="implicit" dans le payload
    - stop     : ne nécessite pas de mastership

Ce module ne gère PAS le mastership — c'est la responsabilité de l'appelant.
Ce module ne fait PAS de polling — voir helpers.py pour les wrappers haut niveau.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from old_abb_rws_client.exceptions import RWSValueError

if TYPE_CHECKING:
    from old_abb_rws_client.client import RWSClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes — routes RWS
# ---------------------------------------------------------------------------

_EXECUTION_BASE: str = "rw/rapid/execution"
_START_PATH: str = f"{_EXECUTION_BASE}/start"
_STOP_PATH: str = f"{_EXECUTION_BASE}/stop"
_RESETPP_PATH: str = f"{_EXECUTION_BASE}/resetpp"

# ---------------------------------------------------------------------------
# Types Literal — valeurs acceptées par l'API RWS ABB
# ---------------------------------------------------------------------------

#: Valeurs possibles du champ ctrlexecstate
CtrlExecState = Literal["running", "stopped"]

#: Modes de reprise après interruption
RegainMode = Literal["continue", "regain", "clear", "enter_consume"]

#: Modes d'exécution
ExecMode = Literal["continue", "step_over", "step_in", "step_out", "step_back",
                   "step_to_last", "step_to_motion"]

#: Modes de cycle
CycleMode = Literal["forever", "as_is", "once"]

#: Conditions de démarrage
StartCondition = Literal["none", "start_at_main"]

#: Modes de stop
StopMode = Literal["stop", "quick_stop", "halt", "soft_stop"]

#: Modes de mastership pour start (implicit = pas besoin d'acquérir manuellement)
MastershipMode = Literal["implicit", "sysop"]


# ---------------------------------------------------------------------------
# Dataclass résultat
# ---------------------------------------------------------------------------


from dataclasses import dataclass  # noqa: E402  (import groupé ici pour lisibilité)


@dataclass(frozen=True)
class ExecutionState:
    """État d'exécution complet retourné par GET /rw/rapid/execution.

    Attributes:
        ctrlexecstate: État principal : "running" ou "stopped".
        cycle:         Mode de cycle actif (ex: "once", "forever").
        excstate:      État étendu du contrôleur (ex: "stopped", "running").
    """
    ctrlexecstate: CtrlExecState
    cycle: str
    excstate: str


# ---------------------------------------------------------------------------
# Extraction depuis la réponse JSON RWS
# ---------------------------------------------------------------------------


def _extract_execution_state(response_json: dict) -> ExecutionState:  # type: ignore[type-arg]
    """Extrait les champs d'état depuis la réponse JSON RWS.

    Structure attendue (GET /rw/rapid/execution?json=1) :
        {
            "state": [
                {
                    "ctrlexecstate": "stopped",
                    "cycle": "once",
                    "excstate": "stopped"
                }
            ]
        }

    Args:
        response_json: Dict issu de response.json().

    Returns:
        ExecutionState peuplé.

    Raises:
        RWSValueError: Structure JSON inattendue.
    """
    try:
        state = response_json["state"][0]
        return ExecutionState(
            ctrlexecstate=state["ctrlexecstate"],
            cycle=state.get("cycle", ""),
            excstate=state.get("excstate", ""),
        )
    except (KeyError, IndexError, TypeError) as exc:
        raise RWSValueError(
            f"Cannot extract execution state from RWS response: "
            f"{response_json!r}"
        ) from exc


# ---------------------------------------------------------------------------
# API publique — GET
# ---------------------------------------------------------------------------


async def get_execution_state(client: RWSClient) -> ExecutionState:
    """Lit l'état d'exécution complet du contrôleur.

    Route : GET /rw/rapid/execution?json=1

    Ne nécessite pas de mastership.

    Args:
        client: Instance RWSClient ouverte.

    Returns:
        ExecutionState avec ctrlexecstate, cycle, excstate.

    Raises:
        RWSValueError: Réponse JSON mal formée.
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            state = await get_execution_state(client)
            if state.ctrlexecstate == "running":
                print("Robot en cours d'exécution")
    """
    logger.debug("GET execution state")
    response = await client.get(_EXECUTION_BASE, params={"json": "1"})

    try:
        data = response.json()
    except Exception as exc:
        raise RWSValueError(
            f"Failed to parse JSON response from execution endpoint: {exc}"
        ) from exc

    state = _extract_execution_state(data)
    logger.debug("Execution state: %s", state)
    return state


async def is_running(client: RWSClient) -> bool:
    """Vérifie si le programme RAPID est en cours d'exécution.

    Wrapper sur get_execution_state() — retourne True si ctrlexecstate == "running".

    Args:
        client: Instance RWSClient ouverte.

    Returns:
        True si running, False si stopped.

    Example:
        ::

            if await is_running(client):
                await stop_execution(client)
    """
    state = await get_execution_state(client)
    return state.ctrlexecstate == "running"


# ---------------------------------------------------------------------------
# API publique — POST start
# ---------------------------------------------------------------------------


async def start_execution(
    client: RWSClient,
    *,
    regain: RegainMode = "continue",
    execmode: ExecMode = "continue",
    cycle: CycleMode = "once",
    condition: StartCondition = "none",
    stopatbp: bool = False,
    alltaskbytsp: bool = False,
) -> None:
    """Démarre l'exécution du programme RAPID.

    Route : POST /rw/rapid/execution/start
            Body : (application/x-www-form-urlencoded)
                regain, execmode, cycle, condition, stopatbp, alltaskbytsp

    ⚠️  Ne pas appeler avec le mastership actif — le contrôleur refusera.
        Utiliser le paramètre mastership=implicit dans le query string
        (géré automatiquement par cette fonction).

    ⚠️  Appeler resetpp() avant start_execution() si le program pointer
        n'est pas positionné sur main.

    Args:
        client: Instance RWSClient ouverte.
        regain: Comportement de reprise après interruption.
                "continue" (défaut) | "regain" | "clear" | "enter_consume"
        execmode: Mode d'exécution pas-à-pas ou continu.
                  "continue" (défaut) | "step_over" | "step_in" | ...
        cycle: Nombre de cycles à exécuter.
               "once" (défaut) | "forever" | "as_is"
        condition: Condition de démarrage.
                   "none" (défaut) | "start_at_main"
        stopatbp: Arrêter aux breakpoints RAPID. Défaut : False.
        alltaskbytsp: Démarrer toutes les tâches via TSP. Défaut : False.

    Returns:
        None — RWS retourne 204 No Content sur succès.

    Raises:
        RWSHTTPError: Erreur contrôleur (ex: 403 si mastership actif).
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            async with Mastership(client):
                await reset_pp(client)
            # mastership libéré AVANT start
            await start_execution(client, cycle="once")
    """
    payload = {
        "regain": regain,
        "execmode": execmode,
        "cycle": cycle,
        "condition": condition,
        "stopatbp": "enabled" if stopatbp else "disabled",
        "alltaskbytsp": "true" if alltaskbytsp else "false",
    }
    logger.debug("POST start execution  payload=%s", payload)
    await client.post(_START_PATH, data=payload, params={"mastership": "implicit"})
    logger.debug("Execution started")


# ---------------------------------------------------------------------------
# API publique — POST stop
# ---------------------------------------------------------------------------


async def stop_execution(
    client: RWSClient,
    *,
    stopmode: StopMode = "stop",
) -> None:
    """Arrête l'exécution du programme RAPID.

    Route : POST /rw/rapid/execution/stop
            Body : stopmode=<mode>   (application/x-www-form-urlencoded)

    Ne nécessite pas de mastership.

    Args:
        client: Instance RWSClient ouverte.
        stopmode: Mode d'arrêt.
                  "stop" (défaut) — arrêt propre en fin d'instruction
                  "quick_stop"   — arrêt rapide
                  "halt"         — arrêt immédiat
                  "soft_stop"    — décélération douce

    Returns:
        None — RWS retourne 204 No Content sur succès.

    Raises:
        RWSHTTPError: Erreur contrôleur.
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            await stop_execution(client)
            await stop_execution(client, stopmode="quick_stop")
    """
    payload = {"stopmode": stopmode}
    logger.debug("POST stop execution  stopmode=%s", stopmode)
    await client.post(_STOP_PATH, data=payload)
    logger.debug("Execution stopped")


# ---------------------------------------------------------------------------
# API publique — POST resetpp
# ---------------------------------------------------------------------------


async def reset_pp(client: RWSClient) -> None:
    """Remet le program pointer sur la procédure main du programme RAPID.

    Route : POST /rw/rapid/execution/resetpp

    ⚠️  Nécessite le mastership RAPID — doit être appelé dans un bloc Mastership.

    Args:
        client: Instance RWSClient ouverte.

    Returns:
        None — RWS retourne 204 No Content sur succès.

    Raises:
        RWSHTTPError: Erreur contrôleur (ex: 403 sans mastership).
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            async with Mastership(client):
                await reset_pp(client)
    """
    logger.debug("POST resetpp")
    await client.post(_RESETPP_PATH)
    logger.debug("Program pointer reset to main")
