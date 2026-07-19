# abb_rws_client/highlevel/rapid.py
"""High-level RAPID wrappers for ABB RWS RobotWare 6.

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
from abb_rws_client_python_rw6.core.exceptions import RWSHTTPError
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.rws.mastership import (
    post_mastership_domain_release,
    post_mastership_domain_request,
)
from abb_rws_client_python_rw6.rws.panel import set_controller_state
from abb_rws_client_python_rw6.rws.rapid.execution import (
    get_rapid_execution_state,
    reset_rapid_program_pointer_to_main,
    start_rapid_execution,
    stop_rapid_execution,
)
from abb_rws_client_python_rw6.rws.rapid.symbol import (
    get_rapid_symbol_data,
    update_rapid_variable_current_value,
)
from abb_rws_client_python_rw6.rws.rapid.tasks import (
    load_rapid_module_into_rapid_task,
    post_unload_module_from_rapid_task,
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


def _parse_symbol_value(response: httpx.Response) -> str:
    """Extract the ``value`` field from a RAPID symbol data response.

    Args:
        response: Raw HTTP response from ``get_rapid_symbol_data``.

    Returns:
        The symbol value as a string (as returned by the controller).

    Raises:
        ValueError: If the value cannot be extracted from the response body.

    Example:
        ```python
        resp = await get_rapid_symbol_data(client, symbolurl="RAPID/T_ROB1/M/x")
        val = _parse_symbol_value(resp)
        # val == "42"
        ```
    """
    # JSON path: {"state": [{"value": "...", ...}]}
    try:
        data = response.json()
        states = data.get("state", [])
        if states and "value" in states[0]:
            return str(states[0]["value"])
    except Exception:
        pass

    # XML / HTML path: <span class="value">...</span>
    match = re.search(
        r'class=["\']value["\'][^>]*>([^<]+)<',
        response.text,
    )
    if match:
        return match.group(1).strip()

    raise ValueError(f"Cannot parse symbol value from response: {response.text[:200]}")


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


# ---------------------------------------------------------------------------
# Mastership-guarded variable write
# ---------------------------------------------------------------------------


async def set_variable_with_mastership(
    client: RWSClient,
    *,
    symbolurl: str,
    value: str,
    domain: str = "rapid",
) -> None:
    """Write a RAPID variable value, acquiring and releasing mastership.

    Composes:

    1. ``post_mastership_domain_request(domain, action="request")``
    2. ``update_rapid_variable_current_value(action="set", value=value)``
    3. ``post_mastership_domain_release(domain, action="release")``

    Mastership is **always** released in a ``finally`` block, even if
    the write fails, to avoid leaving the controller locked.

    Route (delegated):
        - ``POST /rw/mastership/{domain}`` (action=request)
        - ``POST /rw/rapid/symbol/data/{symbolurl}`` (action=set)
        - ``POST /rw/mastership/{domain}`` (action=release)

    ABB constraints:
        - Requires AUTO mode for mastership.
        - ``symbolurl`` format: ``RAPID/T_ROB1/MainModule/my_var``
        - ``domain`` must be one of: ``"rapid"``, ``"cfg"``, ``"motion"``.

    Args:
        client: Open ``RWSClient`` instance.
        symbolurl: Full RAPID symbol path, e.g.
            ``"RAPID/T_ROB1/MainModule/counter"``.
        value: New value as a string. Numeric types must be
            pre-converted: ``str(42)``, ``str(3.14)``.
        domain: Mastership domain. Defaults to ``"rapid"``.

    Returns:
        None. Expects HTTP 204 on the write call.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/target_x",
                value="250.0",
            )
        ```
    """
    # Acquire mastership on the specified domain
    await post_mastership_domain_request(client, domain=domain, action="request")
    try:
        await update_rapid_variable_current_value(
            client,
            symbolurl=symbolurl,
            action="set",
            value=value,
        )
        logger.debug("Variable %s set to %r", symbolurl, value)
    finally:
        # Always release — even on exception — to avoid locking the controller
        await post_mastership_domain_release(client, domain=domain, action="release")


async def set_variables_with_mastership(
    client: RWSClient,
    *,
    values: dict[str, str],
    domain: str = "rapid",
) -> None:
    """Write multiple RAPID variables while holding mastership once.

    Args:
        client: Open RWSClient instance.
        values: Mapping of symbolurl -> value.
        domain: Mastership domain. Defaults to "rapid".

    Returns:
        None.
    """
    await post_mastership_domain_request(client, domain=domain, action="request")
    try:
        for symbolurl, value in values.items():
            await update_rapid_variable_current_value(
                client,
                symbolurl=symbolurl,
                action="set",
                value=value,
            )
            logger.debug("Variable %s set to %r", symbolurl, value)
    finally:
        await post_mastership_domain_release(client, domain=domain, action="release")


async def get_variable(
    client: RWSClient,
    *,
    symbolurl: str,
) -> str:
    """Read a RAPID variable value.

    Wraps ``get_rapid_symbol_data`` and extracts the ``value`` field
    from the response body.

    Route (delegated): ``GET /rw/rapid/symbol/data/{symbolurl}``

    ABB constraints:
        - No mastership required for reads.
        - ``symbolurl`` format: ``RAPID/T_ROB1/MainModule/my_var``

    Args:
        client: Open ``RWSClient`` instance.
        symbolurl: Full RAPID symbol path, e.g.
            ``"RAPID/T_ROB1/MainModule/counter"``.

    Returns:
        The variable value as a string, exactly as returned by the
        controller (e.g. ``"42"``, ``"TRUE"``,
        ``"[[250,0,300],[1,0,0,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]]"``).

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.
        ValueError: If the value cannot be parsed from the response.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            val = await get_variable(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/counter",
            )
            print("counter =", val)
        ```
    """
    response = await get_rapid_symbol_data(client, symbolurl=symbolurl)
    return _parse_symbol_value(response)


# ---------------------------------------------------------------------------
# Module management
# ---------------------------------------------------------------------------


async def load_module_safe(
    client: RWSClient,
    *,
    task: str,
    module_path: str,
    module_name: str,
    domain: str = "rapid",
) -> None:
    """Unload (if present) then load a RAPID module, with mastership.

    Composes:

    1. ``reset_rapid_program_pointer_to_main(action="resetpp")`` — resets
       the program pointer so the controller accepts module load/unload
       operations (ABB requires PP reset before any structural change).
    2. ``post_mastership_domain_request(domain, action="request")``
    3. ``post_unload_module_from_rapid_task(task, action="unloadmod",
       module=module_name)`` — errors are logged but not re-raised
       (module may not be loaded yet).
    4. ``load_rapid_module_into_rapid_task(task, action="loadmod",
       modulepath=module_path)``
    5. ``post_mastership_domain_release(domain, action="release")``

    Mastership is always released in a ``finally`` block.

    Route (delegated):
        - ``POST /rw/rapid/execution`` (action=resetpp)
        - ``POST /rw/mastership/{domain}`` (action=request)
        - ``POST /rw/rapid/tasks/{task}`` (action=unloadmod)
        - ``POST /rw/rapid/tasks/{task}`` (action=loadmod)
        - ``POST /rw/mastership/{domain}`` (action=release)

    ABB constraints:
        - ``resetpp`` must be called before any module load/unload
          operation, even when RAPID is already stopped. Omitting it
          causes HTTP 400 (SYS_CTRL_E_EXEC_STATE).
        - ``module_path`` is a path on the **controller filesystem**,
          e.g. ``"$HOME/my_module.mod"``.
        - ``module_name`` is the RAPID module name (without extension),
          e.g. ``"my_module"``.
        - RAPID mastership required for both load and unload.
        - ``domain`` must be one of: ``"rapid"``, ``"cfg"``, ``"motion"``.

    Args:
        client: Open ``RWSClient`` instance.
        task: RAPID task name, e.g. ``"T_ROB1"``.
        module_path: Full path on the controller filesystem, e.g.
            ``"$HOME/my_module.mod"``.
        module_name: RAPID module name (no extension), e.g.
            ``"my_module"``.
        domain: Mastership domain. Defaults to ``"rapid"``.

    Returns:
        None. Expects HTTP 204 on the load call.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400 (load step only).

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await load_module_safe(
                client,
                task="T_ROB1",
                module_path="$HOME/my_module.mod",
                module_name="my_module",
            )
        ```
    """
    # Step 1 — Reset program pointer BEFORE taking mastership.
    # ABB RW6 rejects loadmod/unloadmod with HTTP 400 (SYS_CTRL_E_EXEC_STATE)
    # if the PP has not been reset, even when RAPID is stopped.
    logger.debug("Resetting program pointer before module load …")
    try:
        await reset_rapid_program_pointer_to_main(client, action="resetpp")
        logger.debug("Program pointer reset OK.")
    except RWSHTTPError as exc:
        # resetpp can fail if no program is loaded yet (first load).
        # This is acceptable — log and continue.
        logger.debug("resetpp skipped (no program loaded yet: %s)", exc)

    # Step 2 — Acquire mastership on the specified domain
    await post_mastership_domain_request(client, domain=domain, action="request")
    try:
        # Step 3 — Attempt unload — silently ignore if module is not loaded
        try:
            await post_unload_module_from_rapid_task(
                client,
                task=task,
                action="unloadmod",
                module=module_name,
            )
            logger.debug("Module %r unloaded from task %r.", module_name, task)
        except RWSHTTPError as exc:
            logger.debug(
                "Unload of %r skipped (not loaded or error: %s).",
                module_name,
                exc,
            )

        # Step 4 — Load the module
        await load_rapid_module_into_rapid_task(
            client,
            task=task,
            action="loadmod",
            modulepath=module_path,
        )
        logger.debug(
            "Module %r loaded into task %r from %r.",
            module_name,
            task,
            module_path,
        )
    finally:
        # Step 5 — Always release mastership, even on exception
        await post_mastership_domain_release(client, domain=domain, action="release")


# ---------------------------------------------------------------------------
# Motor control
# ---------------------------------------------------------------------------


async def set_motors_on(client: RWSClient) -> None:
    """Switch the controller to motors-on state.

    Wraps ``set_controller_state`` with ``ctrl_state="motoron"``.

    Route (delegated): ``POST /rw/panel/ctrlstate`` (action=setctrlstate)

    ABB constraints:
        - Controller must be in AUTO mode.
        - No mastership required.

    Args:
        client: Open ``RWSClient`` instance.

    Returns:
        None. Expects HTTP 204.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_motors_on(client)
        ```
    """
    await set_controller_state(
        client,
        action="setctrlstate",
        ctrl_state="motoron",
    )
    logger.debug("Motors ON")


async def set_motors_off(client: RWSClient) -> None:
    """Switch the controller to motors-off state.

    Wraps ``set_controller_state`` with ``ctrl_state="motoroff"``.

    Route (delegated): ``POST /rw/panel/ctrlstate`` (action=setctrlstate)

    ABB constraints:
        - No mastership required.

    Args:
        client: Open ``RWSClient`` instance.

    Returns:
        None. Expects HTTP 204.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_motors_off(client)
        ```
    """
    await set_controller_state(
        client,
        action="setctrlstate",
        ctrl_state="motoroff",
    )
    logger.debug("Motors OFF")
