# abb_rws_client/highlevel/execution.py
"""High-level RAPID execution control for ABB RWS RobotWare 6.

Author: Clement RACINET

Composed operations built exclusively from atomic ``rws/`` functions.
No HTTP calls are made directly in this module.

All functions are async and require an open ``RWSClient`` instance.
"""

from __future__ import annotations

import asyncio
import re

import httpx

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.rws.rapid.execution import (
    get_rapid_execution_state,
    reset_rapid_program_pointer_to_main,
    start_rapid_execution,
    stop_rapid_execution,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_EXEC_STATE_KEY = "ctrlexecstate"
_RUNNING_VALUE = "running"


def _parse_exec_state(response: httpx.Response) -> str:
    """Extract ``ctrlexecstate`` from a RAPID execution state response.

    ABB RWS returns either XML/HTML (default) or JSON depending on the
    ``Accept`` header sent by the client. Both formats are handled.

    Args:
        response: Raw HTTP response from ``get_rapid_execution_state``.

    Returns:
        The execution state string, e.g. ``"running"`` or ``"stopped"``.

    Raises:
        ValueError: If the state cannot be extracted from the response body.

    Example:
        ```python
        resp = await get_rapid_execution_state(client)
        state = _parse_exec_state(resp)
        # state == "stopped"
        ```
    """
    # JSON path: {"state": [{"ctrlexecstate": "stopped", ...}]}
    try:
        data = response.json()
        states = data.get("state", [])
        if states and _EXEC_STATE_KEY in states[0]:
            return str(states[0][_EXEC_STATE_KEY])
    except Exception:
        pass

    # XML / HTML path: <span class="ctrlexecstate">stopped</span>
    match = re.search(
        r'class=["\']ctrlexecstate["\'][^>]*>([^<]+)<',
        response.text,
    )
    if match:
        return match.group(1).strip()

    raise ValueError(f"Cannot parse ctrlexecstate from response: {response.text[:200]}")


# ---------------------------------------------------------------------------
# Execution state
# ---------------------------------------------------------------------------


async def is_running(client: RWSClient) -> bool:
    """Check whether RAPID execution is currently running.

    Wraps ``get_rapid_execution_state`` and parses the ``ctrlexecstate``
    field from the response.

    Route (delegated): ``GET /rw/rapid/execution``

    Args:
        client: Open ``RWSClient`` instance.

    Returns:
        ``True`` if the controller execution state is ``"running"``,
        ``False`` otherwise (``"stopped"``, ``"idle"``, etc.).

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.
        ValueError: If the execution state cannot be parsed.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            running = await is_running(client)
            print("Running:", running)
        ```
    """
    response = await get_rapid_execution_state(client)
    return _parse_exec_state(response) == _RUNNING_VALUE


# ---------------------------------------------------------------------------
# Start / Stop
# ---------------------------------------------------------------------------


async def start_rapid(
    client: RWSClient,
    *,
    regain: str = "continue",
    execmode: str = "continue",
    cycle: str = "forever",
    condition: str = "none",
    stopatbp: str = "disabled",
    alltaskbytsp: str = "false",
) -> None:
    """Reset the program pointer to main and start RAPID execution.

    Composes ``reset_rapid_program_pointer_to_main`` followed by
    ``start_rapid_execution``. Mastership is not requested explicitly
    because ABB handles it internally for both ``resetpp`` and ``start``
    in RW6 AUTO mode.

    Route (delegated):
        - ``POST /rw/rapid/execution`` (action=resetpp)
        - ``POST /rw/rapid/execution`` (action=start)

    ABB constraints:
        - Controller must be in AUTO mode with motors ON.
        - ``resetpp`` requires mastership; ABB grants it implicitly.

    Args:
        client: Open ``RWSClient`` instance.
        regain: Regain mode. One of ``continue | regain | clear``.
            Defaults to ``"continue"``.
        execmode: Execution mode. One of ``continue | stepin | stepover
            | stepout | stepback | steplast | stepmotion``.
            Defaults to ``"continue"``.
        cycle: Cycle mode. One of ``forever | asis | once``.
            Defaults to ``"forever"``.
        condition: Condition. One of ``none | callchain``.
            Defaults to ``"none"``.
        stopatbp: Stop at breakpoint. One of ``disabled | enabled``.
            Defaults to ``"disabled"``.
        alltaskbytsp: All tasks by TSP. One of ``true | false``.
            Defaults to ``"false"``.

    Returns:
        None. Both underlying calls expect HTTP 204.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await start_rapid(client, cycle="once")
        ```
    """
    await reset_rapid_program_pointer_to_main(client, action="resetpp")
    await start_rapid_execution(
        client,
        action="start",
        regain=regain,
        execmode=execmode,
        cycle=cycle,
        condition=condition,
        stopatbp=stopatbp,
        alltaskbytsp=alltaskbytsp,
    )
    logger.debug("RAPID execution started (cycle=%s)", cycle)


async def stop_rapid(
    client: RWSClient,
    *,
    stopmode: str = "stop",
) -> None:
    """Stop RAPID execution.

    Wraps ``stop_rapid_execution`` with ``action="stop"``.

    Route (delegated): ``POST /rw/rapid/execution`` (action=stop)

    ABB constraints:
        - No mastership required to stop.

    Args:
        client: Open ``RWSClient`` instance.
        stopmode: Stop mode. One of ``stop | qstop | halt``.
            Defaults to ``"stop"``.

    Returns:
        None. Expects HTTP 204.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await stop_rapid(client)
        ```
    """
    await stop_rapid_execution(client, action="stop", stopmode=stopmode)
    logger.debug("RAPID execution stopped (stopmode=%s)", stopmode)


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------


async def wait_until_stopped(
    client: RWSClient,
    *,
    poll_interval: float = 0.2,
    timeout: float | None = None,
) -> None:
    """Poll until RAPID execution is no longer running.

    Repeatedly calls ``get_rapid_execution_state`` until
    ``ctrlexecstate`` is no longer ``"running"``, or until the optional
    timeout is exceeded.

    Route (delegated): ``GET /rw/rapid/execution``

    ABB constraints:
        - Polling-based; no WebSocket/subscription used.
        - ``poll_interval`` should be ≥ 0.1 s to avoid flooding the
          controller.

    Args:
        client: Open ``RWSClient`` instance.
        poll_interval: Seconds between each poll. Defaults to ``0.2``.
        timeout: Maximum seconds to wait. ``None`` means wait forever.
            Defaults to ``None``.

    Returns:
        None. Returns as soon as the controller is no longer running.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.
        TimeoutError: If ``timeout`` is set and exceeded before the
            controller stops.
        ValueError: If the execution state cannot be parsed.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await start_rapid(client, cycle="once")
            await wait_until_stopped(client, timeout=30.0)
            print("Program finished.")
        ```
    """
    elapsed = 0.0
    while True:
        if not await is_running(client):
            return
        if timeout is not None and elapsed >= timeout:
            raise TimeoutError(
                f"RAPID still running after {timeout}s (poll_interval={poll_interval}s)"
            )
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
