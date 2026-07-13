# exemples/05/example_io_signal.py
"""Example 05 — Read and write digital IO signals.

Demonstrates:
    - Listing all IO signals via ``get_io_signals``.
    - Searching a specific signal by name via ``post_signal_search``.
    - Reading the ``lvalue`` from the search response.

Note on write access:
    The write endpoint is:
        ``POST /rw/iosystem/signals/{network}/{unit}/{signal}?action=set``
    The ``network`` and ``unit`` names required for the path are
    controller-specific. See the inline comment in ``main()`` for the
    raw call pattern once those values are known.

Prerequisites:
    - Controller with at least one configured digital output (DO).
    - ``.env`` at the repository root with ``RWS_HOST``, ``RWS_USER``,
      ``RWS_PASSWORD``, ``RWS_SIGNAL_NAME`` (optional — defaults apply).

RAPID side:
    None required.

Run:
    pixi run python exemples/05/example_io_signal.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

import httpx

from abb_rws_client import (
    RWSClient,
    RWSError,
    configure_logging,
    get_logger,
    load_env,
)
from abb_rws_client.rws.iosystem.signals import get_io_signals, post_signal_search

load_env()
configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))
logger = get_logger("examples.io_signal")


def _parse_lvalue(response: httpx.Response) -> str:
    """Extract the ``lvalue`` from a signal search response.

    Handles both JSON and XML/HTML responses from different RW6 firmware
    versions.

    Args:
        response: Raw HTTP response from ``post_signal_search``.

    Returns:
        Signal logical value as string (``"0"`` or ``"1"`` for digital
        signals).

    Raises:
        ValueError: If the value cannot be extracted from the response body.

    Example:
        ```python
        val = _parse_lvalue(resp)  # "0" or "1"
        ```
    """
    try:
        data = response.json()
        states = data.get("state", [])
        if states and "lvalue" in states[0]:
            return str(states[0]["lvalue"])
    except Exception:
        pass

    match = re.search(r'class=["\']lvalue["\'][^>]*>([^<]+)<', response.text)
    if match:
        return match.group(1).strip()

    raise ValueError(
        f"Cannot parse lvalue from signal response: {response.text[:200]}"
    )


async def main() -> None:
    """Run the IO signal example."""
    signal_name = os.getenv("RWS_SIGNAL_NAME", "DO_EXAMPLE")

    logger.info("Connecting to controller …")
    logger.info("Target signal: %r", signal_name)

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            logger.info("Fetching signal list …")
            resp_list = await get_io_signals(client)
            logger.info(
                "HTTP %s — %d bytes received",
                resp_list.status_code,
                len(resp_list.text),
            )

            logger.info("Searching for signal %r …", signal_name)
            resp_search = await post_signal_search(
                client,
                action="signal-search",
                name=signal_name,
            )
            logger.info("HTTP %s", resp_search.status_code)

            current = _parse_lvalue(resp_search)
            logger.info("Current value: %r", current)

            # Write pattern (requires network + unit names from your config):
            #
            #   network = "Local"          # adapt to your controller
            #   unit    = "PANEL"          # adapt to your controller
            #   new_value = "0" if current == "1" else "1"
            #   await client.post(
            #       f"/rw/iosystem/signals/{network}/{unit}/{signal_name}",
            #       params={"action": "set"},
            #       data={"lvalue": new_value},
            #   )

            logger.info("Done.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
