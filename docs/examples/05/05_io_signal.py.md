# 05 Io Signal

Source file: `05_io_signal.py`

````python
# examples/05/example_io_signal.py
"""Example 05 — Read and write a virtual digital output signal (TEST_DO_RWS).

Author: Clement RACINET

Demonstrates:
    - Listing all IO signals via ``get_io_signals``.
    - Searching a specific signal by name via ``post_signal_search``.
    - Reading the ``lvalue`` of the signal via a direct GET.
    - Writing a new value via POST with ``action=set``.
    - Toggling the signal so the RAPID module can detect the change.

Prerequisites:
    - A virtual digital output ``TEST_DO_RWS`` configured in the IO system
      under a Virtual unit (e.g. ``VIRTUAL1``).
    - The RAPID module ``ExampleIOSignal`` loaded and running on ``T_ROB1``.
    - ``.env`` at the repository root with ``RWS_HOST``, ``RWS_USER``,
      ``RWS_PASSWORD``.

RAPID side:
    ``examples/05/IOSignal.mod`` — waits for ``TEST_DO_RWS`` to go HIGH
    via ``WaitUntil DOutput(...) = 1``.

Run:
    pixi run python examples/05/example_io_signal.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

import httpx

from abb_rws_client_python_rw6 import (
    RWSClient,
    RWSError,
    configure_logging,
    get_logger,
    load_env,
)
from abb_rws_client_python_rw6.rws.iosystem.signals import get_io_signals, post_signal_search

load_env()
configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))
logger = get_logger("examples.io_signal")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_signal_href(response: httpx.Response, signal_name: str) -> str:
    """Extract the canonical absolute href of a named signal from a search response.

    The RW6 search response body is an HTML document whose ``<base href>`` is
    set to ``http://<host>/rw/iosystem/``. Signal links are therefore
    **relative** (e.g. ``signals/Virtual/VIRTUAL1/TEST_DO_RWS``), not absolute.
    This function extracts the matching href and normalises it to an absolute
    path suitable for a direct ``GET`` or ``POST`` via ``RWSClient``.

    Args:
        response: Raw HTTP response from ``post_signal_search``.
        signal_name: Exact signal name to locate (case-sensitive).

    Returns:
        Absolute URL path to the signal resource, e.g.
        ``"/rw/iosystem/signals/Virtual/VIRTUAL1/TEST_DO_RWS"``.

    Raises:
        ValueError: If no href matching ``signal_name`` is found in the
            response body.

    Example:
        ```python
        href = _parse_signal_href(resp_search, "TEST_DO_RWS")
        # "/rw/iosystem/signals/Virtual/VIRTUAL1/TEST_DO_RWS"
        ```
    """
    # RW6 response format (relative href, base = /rw/iosystem/):
    # <a href="signals/Virtual/VIRTUAL1/TEST_DO_RWS" rel="self"></a>
    pattern = rf'href=["\']([^"\']*/{re.escape(signal_name)}(?:;[^"\']*)?)["\']'
    match = re.search(pattern, response.text)
    if not match:
        raise ValueError(
            f"Signal {signal_name!r} not found in search response. "
            f"Body excerpt: {response.text[:300]}"
        )
    # Strip any ;state suffix and query parameters — keep the clean path
    href = match.group(1).split(";")[0].split("?")[0]

    # Normalise to absolute path — RW6 base is /rw/iosystem/
    if not href.startswith("/"):
        href = "/rw/iosystem/" + href

    return href


def _parse_lvalue(response: httpx.Response) -> str:
    """Extract the ``lvalue`` from a direct signal GET response.

    Args:
        response: Raw HTTP response from a direct ``GET`` on a signal URL.

    Returns:
        Signal logical value as string (``"0"`` or ``"1"`` for digital signals).

    Raises:
        ValueError: If the value cannot be extracted from the response body.

    Example:
        ```python
        resp = await client.get("/rw/iosystem/signals/Virtual/VIRTUAL1/TEST_DO_RWS")
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

    raise ValueError(f"Cannot parse lvalue from signal response: {response.text[:200]}")


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the IO signal read/write example against TEST_DO_RWS.

    Sequence:
        1. List all IO signals (sanity check).
        2. Search for TEST_DO_RWS and resolve its canonical href.
        3. Read current value.
        4. Write 1 → RAPID module detects HIGH and logs on FlexPendant.
        5. Read back to confirm.
        6. Write 0 → reset to known state.
        7. Read back final value.
    """
    signal_name = os.getenv("RWS_SIGNAL_NAME", "TEST_DO_RWS")
    logger.info("Connecting to controller …")
    logger.info("Target signal: %r", signal_name)

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            # ------------------------------------------------------------------
            # 1. List all signals (sanity check)
            # ------------------------------------------------------------------
            logger.info("Fetching signal list …")
            resp_list = await get_io_signals(client)
            logger.info(
                "HTTP %s — %d bytes received",
                resp_list.status_code,
                len(resp_list.text),
            )

            # ------------------------------------------------------------------
            # 2. Search signal by name → resolve canonical href
            # ------------------------------------------------------------------
            logger.info("Searching for signal %r …", signal_name)
            resp_search = await post_signal_search(
                client,
                action="signal-search",
                name=signal_name,
            )
            logger.info("HTTP %s (search)", resp_search.status_code)

            signal_href = _parse_signal_href(resp_search, signal_name)
            logger.info("Signal href: %s", signal_href)

            # ------------------------------------------------------------------
            # 3. Read current value
            # ------------------------------------------------------------------
            resp_get = await client.get(signal_href)
            logger.info("HTTP %s (GET)", resp_get.status_code)
            value_before = _parse_lvalue(resp_get)
            logger.info("Value before write: %r", value_before)

            # ------------------------------------------------------------------
            # 4. Write 1 — RAPID WaitUntil will unblock
            # ------------------------------------------------------------------
            logger.info("Writing 1 to %r …", signal_name)
            resp_set = await client.post(
                signal_href,
                params={"action": "set"},
                data={"lvalue": "1"},
            )
            logger.info("HTTP %s (SET → 1)", resp_set.status_code)

            # ------------------------------------------------------------------
            # 5. Read back to confirm
            # ------------------------------------------------------------------
            resp_get2 = await client.get(signal_href)
            value_after = _parse_lvalue(resp_get2)
            logger.info("Value after write 1: %r", value_after)

            # ------------------------------------------------------------------
            # 6. Write 0 — reset to known state
            # ------------------------------------------------------------------
            logger.info("Resetting %r to 0 …", signal_name)
            resp_reset = await client.post(
                signal_href,
                params={"action": "set"},
                data={"lvalue": "0"},
            )
            logger.info("HTTP %s (SET → 0)", resp_reset.status_code)

            # ------------------------------------------------------------------
            # 7. Read back final value
            # ------------------------------------------------------------------
            resp_get3 = await client.get(signal_href)
            value_final = _parse_lvalue(resp_get3)
            logger.info("Final value: %r", value_final)

            logger.info("Done.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
````
