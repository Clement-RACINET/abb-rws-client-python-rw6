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


#  Helpers

def _parse_signal_href(response: httpx.Response, signal_name: str) -> str:
    """Extract the canonical href of a named signal from a search response.

    The search response body contains HTML/XML with ``<a href="...">`` links
    pointing to each matched signal. This function extracts the path for the
    signal whose name matches ``signal_name`` exactly.

    Args:
        response: Raw HTTP response from ``post_signal_search``.
        signal_name: Exact signal name to locate (case-sensitive).

    Returns:
        Relative URL path to the signal resource, e.g.
        ``"/rw/iosystem/signals/Local/PANEL/DO_EXAMPLE"``.

    Raises:
        ValueError: If no href matching ``signal_name`` is found.

    Example:
        ```python
        href = _parse_signal_href(resp_search, "DO_EXAMPLE")
        # "/rw/iosystem/signals/Local/PANEL/DO_EXAMPLE"
        ```
    """
    # RW6 response format:
    # <a href="/rw/iosystem/signals/Local/PANEL/DO_EXAMPLE;state">DO_EXAMPLE</a>
    # We match the href that ends with /{signal_name} or /{signal_name};state
    pattern = rf'href=["\']([^"\']*/{re.escape(signal_name)}(?:;[^"\']*)?)["\']'
    match = re.search(pattern, response.text)
    if not match:
        raise ValueError(
            f"Signal {signal_name!r} not found in search response. "
            f"Body excerpt: {response.text[:300]}"
        )
    # Strip any ;state suffix and query parameters — keep the clean path
    href = match.group(1).split(";")[0].split("?")[0]
    return href


def _parse_lvalue(response: httpx.Response) -> str:
    """Extract the ``lvalue`` from a direct signal GET response.

    This function must be called on the response of a ``GET`` to the
    signal's canonical URL (e.g. ``GET /rw/iosystem/signals/{net}/{unit}/{name}``),
    **not** on a search response.

    Handles both JSON and XML/HTML responses from different RW6 firmware
    versions.

    Args:
        response: Raw HTTP response from a direct ``GET`` on a signal URL.

    Returns:
        Signal logical value as string (``"0"`` or ``"1"`` for digital
        signals).

    Raises:
        ValueError: If the value cannot be extracted from the response body.

    Example:
        ```python
        resp = await client.get("/rw/iosystem/signals/Local/PANEL/DO_EXAMPLE")
        val = _parse_lvalue(resp)
        # "0" or "1"
        ```
    """
    # JSON path: {"state": [{"lvalue": "0", ...}]}
    try:
        data = response.json()
        states = data.get("state", [])
        if states and "lvalue" in states[0]:
            return str(states[0]["lvalue"])
    except Exception:
        pass

    # XML / HTML path: <span class="lvalue">0</span>
    match = re.search(r'class=["\']lvalue["\'][^>]*>([^<]+)<', response.text)
    if match:
        return match.group(1).strip()

    raise ValueError(
        f"Cannot parse lvalue from signal response: {response.text[:200]}"
    )


# main()

async def main() -> None:
    """Run the IO signal example."""
    #signal_name = os.getenv("RWS_SIGNAL_NAME", "DO_EXAMPLE") [DEBUG]
    signal_name = os.getenv("RWS_SIGNAL_NAME", "PCorpAKD_GI_MotorTemperature")
    logger.info("Connecting to controller …")
    logger.info("Target signal: %r", signal_name)

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            #  1. List all signals
            logger.info("Fetching signal list …")
            resp_list = await get_io_signals(client)
            logger.info(
                "HTTP %s — %d bytes received",
                resp_list.status_code,
                len(resp_list.text),
            )

            # DEBUG TEMPORAIRE — à supprimer après
            logger.info("Signal list body:\n%s", resp_list.text[:])


            #  2. Search the signal by name to get its canonical href
            # post_signal_search returns a FILTERED LIST of signal links,
            # NOT a lvalue. We must extract the href and GET the signal
            # directly to read its value.
            logger.info("Searching for signal %r …", signal_name)
            resp_search = await post_signal_search(
                client,
                action="signal-search",
                name=signal_name,
            )
            logger.info("HTTP %s (search)", resp_search.status_code)

            # Extract the canonical path from the search result links
            signal_href = _parse_signal_href(resp_search, signal_name)
            logger.debug("Signal href: %s", signal_href)

            #  3. GET the signal directly to read its lvalue
            resp_signal = await client.get(signal_href)
            logger.info("HTTP %s (direct GET)", resp_signal.status_code)

            current = _parse_lvalue(resp_signal)
            logger.info("Current value of %r: %r", signal_name, current)

            #  4. Write pattern (requires network + unit from your config)
            # Uncomment and adapt once network/unit names are known:
            #
            # network = "Local"   # adapt to your controller
            # unit    = "PANEL"   # adapt to your controller
            # new_value = "0" if current == "1" else "1"
            # await client.post(
            #     f"/rw/iosystem/signals/{network}/{unit}/{signal_name}",
            #     params={"action": "set"},
            #     data={"lvalue": new_value},
            # )
            # logger.info("Signal %r set to %r", signal_name, new_value)

            logger.info("Done.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
