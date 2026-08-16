# Example Start Stop

Source file: `example_start_stop.py`

```python
# examples/02/example_start_stop.py
"""Example 02 — Start and stop RAPID execution.

Author: Clement RACINET

Prerequisites:
    - Controller in AUTO mode, motors ON.
    - A RAPID program loaded in T_ROB1 with a ``main()`` procedure.
    - ``.env`` at the repository root with ``RWS_HOST``, ``RWS_USER``,
      ``RWS_PASSWORD`` (optional — defaults apply if absent).

RAPID side:
    See ``examples/02/StartStop.mod``.

Run:
    pixi run python examples/02/example_start_stop.py
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
from abb_rws_client_python_rw6.highlevel.execution import (
    is_running,
    start_rapid,
    stop_rapid,
    wait_until_stopped,
)

load_env()
configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))
logger = get_logger("examples.start_stop")


async def main() -> None:
    """Run the start/stop example."""
    logger.info("Connecting to controller …")

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            running = await is_running(client)
            logger.info("Initial state: %s", "RUNNING" if running else "STOPPED")

            if running:
                logger.info("Already running — stopping first …")
                await stop_rapid(client)
                await wait_until_stopped(client, timeout=10.0)
                logger.info("Stopped.")

            logger.info("Starting RAPID (cycle=once) …")
            await start_rapid(client, cycle="once")
            logger.info("Start command sent.")

            logger.info("Waiting for program to finish …")
            await wait_until_stopped(client, poll_interval=0.5)
            logger.info("Program finished (state=stopped).")

    except TimeoutError:
        logger.error("Timeout: program did not stop within the allowed time.")
        sys.exit(1)
    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```
