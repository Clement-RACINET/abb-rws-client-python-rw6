# examples/03/example_read_write_variable.py
"""Example 03 — Read and write a RAPID variable.

Author: Clement RACINET

Demonstrates:
    - Reading a RAPID VAR/PERS via ``get_variable`` (highlevel).
    - Writing a RAPID VAR/PERS via ``set_variable_with_mastership`` (highlevel).

Prerequisites:
    - Controller in AUTO mode.
    - Module ``ReadWriteVariable`` loaded in T_ROB1
      (see ``examples/03/ReadWriteVariable.mod``).
    - ``.env`` at the repository root with ``RWS_HOST``, ``RWS_USER``,
      ``RWS_PASSWORD``, ``RWS_RAPID_TASK`` (optional — defaults apply).

RAPID side:
    See ``examples/03/ReadWriteVariable.mod``.

Run:
    pixi run python examples/03/example_read_write_variable.py
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
from abb_rws_client_python_rw6.highlevel.variables import get_variable, set_variable_with_mastership

load_env()
configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))
logger = get_logger("examples.read_write_variable")


async def main() -> None:
    """Run the read/write variable example."""
    task = os.getenv("RWS_RAPID_TASK", "T_ROB1")
    module = "ReadWriteVariable"

    sym_counter = f"RAPID/{task}/{module}/gCounter"
    sym_message = f"RAPID/{task}/{module}/gMessage"
    sym_enabled = f"RAPID/{task}/{module}/gEnabled"

    logger.info("Connecting to controller …")

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            logger.info("Reading current values …")
            counter = await get_variable(client, symbolurl=sym_counter)
            message = await get_variable(client, symbolurl=sym_message)
            enabled = await get_variable(client, symbolurl=sym_enabled)

            logger.info("  gCounter = %r", counter)
            logger.info("  gMessage = %r", message)
            logger.info("  gEnabled = %r", enabled)

            new_counter = str(int(counter) + 1) if counter.isdigit() else "1"

            logger.info("Writing gCounter = %s …", new_counter)
            await set_variable_with_mastership(client, symbolurl=sym_counter, value=new_counter)

            logger.info('Writing gMessage = "Hello from Python" …')
            await set_variable_with_mastership(
                client, symbolurl=sym_message, value='"Hello from Python"'
            )

            logger.info("Writing gEnabled = TRUE …")
            await set_variable_with_mastership(client, symbolurl=sym_enabled, value="TRUE")

            logger.info("Verifying …")
            counter_after = await get_variable(client, symbolurl=sym_counter)
            message_after = await get_variable(client, symbolurl=sym_message)
            enabled_after = await get_variable(client, symbolurl=sym_enabled)

            logger.info("  gCounter = %r  (was %r)", counter_after, counter)
            logger.info("  gMessage = %r", message_after)
            logger.info("  gEnabled = %r", enabled_after)
            logger.info("Done.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
