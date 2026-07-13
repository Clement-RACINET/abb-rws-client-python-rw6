# exemples/01/example_ping.py
"""Example 01 — Ping: verify connectivity and read controller state.

Prerequisites:
    - ``.env`` at the repository root with ``RWS_HOST``, ``RWS_USER``,
      ``RWS_PASSWORD`` (optional — defaults apply if absent).
    - Controller reachable on the network.

RAPID side:
    None required (read-only, no program needed).

Run:
    pixi run python exemples/01/example_ping.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

import httpx

from abb_rws_client import (
    RWSClient,
    RWSConnectionError,
    RWSError,
    configure_logging,
    get_logger,
    load_env,
)
from abb_rws_client.rws.panel import get_controller_state, get_operation_mode

load_env()
configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))
logger = get_logger("examples.ping")


def _extract_class_value(response: httpx.Response, css_class: str) -> str:
    """Extract the ``title`` attribute of the first element with a given CSS class.

    ABB RWS RobotWare 6 returns XML/HTML by default. State values are
    encoded as ``title`` attributes on ``<li>`` elements whose ``class``
    matches the resource name.

    Args:
        response: Raw HTTP response from a RWS panel endpoint.
        css_class: CSS class name to search for (e.g. ``"pnl-ctrlstate"``).

    Returns:
        The ``title`` value as a string, or ``"<not found>"`` if absent.

    Example:
        ```python
        state = _extract_class_value(resp, "pnl-ctrlstate")
        ```
    """
    match = re.search(
        rf'class="{re.escape(css_class)}"[^>]*title="([^"]+)"',
        response.text,
    )
    if match:
        return match.group(1)
    match = re.search(
        rf'class="{re.escape(css_class)}"[^>]*>([^<]+)<',
        response.text,
    )
    if match:
        return match.group(1).strip()
    return "<not found>"


async def main() -> None:
    """Run the ping example."""
    logger.info("Connecting to controller …")

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            resp_state = await get_controller_state(client)
            ctrl_state = _extract_class_value(resp_state, "pnl-ctrlstate")
            logger.info("ctrlstate : %s", ctrl_state)

            resp_mode = await get_operation_mode(client)
            op_mode = _extract_class_value(resp_mode, "pnl-opmode")
            logger.info("opmode    : %s", op_mode)

            logger.info("─── Summary ───────────────────────────")
            logger.info("  Host      : %s", client.host)
            logger.info("  ctrlstate : %s", ctrl_state)
            logger.info("  opmode    : %s", op_mode)

    except RWSConnectionError as exc:
        logger.error("Cannot reach controller: %s", exc)
        sys.exit(1)
    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
