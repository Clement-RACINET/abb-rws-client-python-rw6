# exemples/04/example_load_module.py
"""Example 04 — Load a RAPID module into a task at runtime.

Author: Clement RACINET

Demonstrates:
    - Using ``load_module_safe`` (highlevel) to unload/load with mastership.

Prerequisites:
    - Controller in AUTO mode, RAPID stopped.
    - Module file already present on the controller at ``RWS_MODULE_PATH``
      (upload it beforehand via FTP, USB, or RWS fileservice).
    - ``.env`` at the repository root with ``RWS_HOST``, ``RWS_USER``,
      ``RWS_PASSWORD``, ``RWS_RAPID_TASK``, ``RWS_MODULE_PATH`` (optional).

RAPID side:
    See ``exemples/04/LoadModule.mod``.

Run:
    pixi run python exemples/04/example_load_module.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from abb_rws_client_python_rw6 import (
    RWSClient,
    RWSError,
    configure_logging,
    get_logger,
    load_env,
)
from abb_rws_client_python_rw6.highlevel.rapid import is_running, load_module_safe, stop_rapid

load_env()
configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))
logger = get_logger("examples.load_module")


async def main() -> None:
    """Run the load module example."""
    task = os.getenv("RWS_RAPID_TASK", "T_ROB1")
    module_name = "LoadModule"
    # actual path on the controller, local overload
    controller_path = os.getenv(
        "RWS_MODULE_PATH",
        "$HOME/000_TESTS/RWS_test/2026_test/LoadModule/LoadModule.mod",
    )

    logger.info("Connecting to controller …")
    logger.info("Module     : %s", module_name)
    logger.info("Controller : %s", controller_path)
    logger.info("Task       : %s", task)

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            if await is_running(client):
                logger.info("RAPID is running — stopping before load …")
                await stop_rapid(client)
                logger.info("RAPID stopped.")

            logger.info("Loading %s into %s …", module_name, task)
            await load_module_safe(
                client,
                task=task,
                module_name=module_name,
                module_path=controller_path,
            )
            logger.info(
                "Module '%s' loaded successfully into %s.", module_name, task
            )
            logger.info("You can now run example 02 to execute it.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
