# abb_rws_client/highlevel/modules.py
"""High-level RAPID module load/unload for ABB RWS RobotWare 6.

Author: Clement RACINET

Composed operations built exclusively from atomic ``rws/`` functions.
No HTTP calls are made directly in this module.

All functions are async and require an open ``RWSClient`` instance.
"""

from __future__ import annotations

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.exceptions import RWSHTTPError
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.rws.mastership import (
    post_mastership_domain_release,
    post_mastership_domain_request,
)
from abb_rws_client_python_rw6.rws.rapid.execution import (
    reset_rapid_program_pointer_to_main,
)
from abb_rws_client_python_rw6.rws.rapid.tasks import (
    load_rapid_module_into_rapid_task,
    post_unload_module_from_rapid_task,
)

logger = get_logger(__name__)


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
