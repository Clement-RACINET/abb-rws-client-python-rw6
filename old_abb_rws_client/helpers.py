# abb_rws_client/helpers.py
"""
Wrappers haut niveau composant plusieurs appels RWS.

Ce module regroupe les patterns d'usage fréquents qui combinent plusieurs
appels atomiques de l'API RWS. Il ne contient aucun endpoint direct —
tout passe par les modules sous-jacents (execution.py, rapid_variable.py, etc.).

Fonctions disponibles :
    reset_and_start()   → resetpp + start en séquence correcte (mastership géré)
    wait_until_stopped() → polling sur get_execution_state jusqu'à "stopped"
    wait_for_var()      → polling sur get_rapid_var jusqu'à une valeur cible

Conventions :
    - Les fonctions de polling acceptent timeout_s et poll_interval_s
    - RWSTimeoutError est levée si le timeout est dépassé
    - Toutes les fonctions sont async
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from old_abb_rws_client.exceptions import RWSTimeoutError
from old_abb_rws_client.execution import get_execution_state, reset_pp, start_execution
from old_abb_rws_client.mastership import Mastership
from old_abb_rws_client.rapid_variable import RapidValue, get_rapid_var

if TYPE_CHECKING:
    from old_abb_rws_client.client import RWSClient
    from old_abb_rws_client.execution import CycleMode, ExecMode, RegainMode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

#: Timeout par défaut pour les opérations de polling (secondes)
DEFAULT_TIMEOUT_S: float = 30.0

#: Intervalle de polling par défaut (secondes)
DEFAULT_POLL_INTERVAL_S: float = 0.2


# ---------------------------------------------------------------------------
# Helpers d'exécution
# ---------------------------------------------------------------------------


async def reset_and_start(
    client: RWSClient,
    *,
    regain: RegainMode = "continue",
    execmode: ExecMode = "continue",
    cycle: CycleMode = "once",
) -> None:
    """Remet le PP sur main puis démarre l'exécution RAPID.

    Séquence correcte ABB RW6 :
        1. Acquérir le mastership
        2. POST /rw/rapid/execution/resetpp
        3. Libérer le mastership  ← OBLIGATOIRE avant start
        4. POST /rw/rapid/execution/start?mastership=implicit

    ⚠️  Le mastership doit être libéré avant start_execution —
        cette fonction gère la séquence correctement.

    Args:
        client: Instance RWSClient ouverte.
        regain: Mode de reprise. Défaut : "continue".
        execmode: Mode d'exécution. Défaut : "continue".
        cycle: Mode de cycle. Défaut : "once".

    Returns:
        None

    Raises:
        MastershipDenied: Mastership refusé (programme en cours ?).
        RWSHTTPError: Erreur contrôleur lors du start.
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            await reset_and_start(client)
            await reset_and_start(client, cycle="forever")
    """
    logger.debug("reset_and_start: acquiring mastership for resetpp")
    async with Mastership(client):
        await reset_pp(client)
    # Mastership libéré ici — start_execution utilise mastership=implicit
    logger.debug("reset_and_start: mastership released, starting execution")
    await start_execution(client, regain=regain, execmode=execmode, cycle=cycle)
    logger.debug("reset_and_start: done")


# ---------------------------------------------------------------------------
# Helpers de polling
# ---------------------------------------------------------------------------


async def wait_until_stopped(
    client: RWSClient,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
) -> None:
    """Attend que l'exécution RAPID soit arrêtée (ctrlexecstate == "stopped").

    Poll GET /rw/rapid/execution?json=1 à intervalle régulier.

    Args:
        client: Instance RWSClient ouverte.
        timeout_s: Timeout total en secondes. Défaut : 30.0.
        poll_interval_s: Intervalle entre deux polls. Défaut : 0.2s.

    Returns:
        None — retourne dès que l'état est "stopped".

    Raises:
        RWSTimeoutError: Timeout dépassé avant que l'état soit "stopped".
        RWSConnectionError: Impossible de joindre le contrôleur.

    Example:
        ::

            await reset_and_start(client)
            await wait_until_stopped(client, timeout_s=60.0)
            print("Programme terminé")
    """
    logger.debug(
        "wait_until_stopped: timeout=%.1fs  poll=%.2fs",
        timeout_s, poll_interval_s,
    )
    elapsed = 0.0
    while elapsed < timeout_s:
        state = await get_execution_state(client)
        if state.ctrlexecstate == "stopped":
            logger.debug("wait_until_stopped: stopped after %.2fs", elapsed)
            return
        await asyncio.sleep(poll_interval_s)
        elapsed += poll_interval_s

    raise RWSTimeoutError(
        f"wait_until_stopped: execution still running after {timeout_s}s"
    )


async def wait_for_var(
    client: RWSClient,
    var: str,
    rapid_type: str,
    expected: RapidValue,
    *,
    module: str,
    task: str = "T_ROB1",
    timeout_s: float = DEFAULT_TIMEOUT_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
) -> None:
    """Attend qu'une variable RAPID atteigne une valeur cible.

    Poll GET /rw/rapid/symbol/data/... à intervalle régulier.

    Cas d'usage typique : attendre qu'un flag booléen RAPID passe à TRUE
    pour signaler la fin d'une opération robot.

    Args:
        client: Instance RWSClient ouverte.
        var: Nom de la variable RAPID à surveiller.
        rapid_type: Type RAPID de la variable (ex: "bool", "num").
        expected: Valeur cible à atteindre.
        module: Module RAPID contenant la variable (obligatoire).
        task: Tâche RAPID. Défaut : "T_ROB1".
        timeout_s: Timeout total en secondes. Défaut : 30.0.
        poll_interval_s: Intervalle entre deux polls. Défaut : 0.2s.

    Returns:
        None — retourne dès que la variable atteint la valeur attendue.

    Raises:
        RWSTimeoutError: Timeout dépassé avant que la variable atteigne expected.
        RWSValueError: Type inconnu ou réponse mal formée.
        RWSConnectionError: Impossible de joindre le contrôleur.

    Example:
        ::

            # Attendre que le flag RAPID "READY" passe à TRUE
            await wait_for_var(
                client, "READY", "bool", True,
                module="MYMOD", timeout_s=60.0,
            )
    """
    logger.debug(
        "wait_for_var: var=%s  expected=%r  timeout=%.1fs",
        var, expected, timeout_s,
    )
    elapsed = 0.0
    while elapsed < timeout_s:
        value = await get_rapid_var(client, var, rapid_type, module=module, task=task)
        if value == expected:
            logger.debug("wait_for_var: '%s' == %r after %.2fs", var, expected, elapsed)
            return
        await asyncio.sleep(poll_interval_s)
        elapsed += poll_interval_s

    raise RWSTimeoutError(
        f"wait_for_var: '{var}' did not reach {expected!r} within {timeout_s}s"
    )
