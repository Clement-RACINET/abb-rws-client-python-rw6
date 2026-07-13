# exemples/05_io_signal.py
"""Example 05 — Read and write digital IO signals.

Demonstrates:
    - Listing all IO signals via get_io_signals
    - Searching a specific signal by name via post_signal_search
    - Reading the lvalue from the search response

Note on write access:
    The write endpoint is:
        POST /rw/iosystem/signals/{network}/{unit}/{signal}?action=set
    The generated rws/ layer does not yet expose a dedicated per-signal
    write function.  The network and unit names required for the path
    are controller-specific.  See the inline comment in main() for the
    raw call pattern once those values are known.

Prerequisites:
    - Controller with at least one configured digital output (DO)
    - .env with ROBOT_IP, RWS_USER, RWS_PASSWORD
    - Set RWS_SIGNAL_NAME to match a real signal on your controller

RAPID side: see exemples/05_io_signal.mod

Run:
    pixi run python exemples/05_io_signal.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

from _env import load_env
import httpx

from abb_rws_client import RWSClient, RWSError
from abb_rws_client.rws.iosystem.signals import get_io_signals, post_signal_search


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
    load_env()

    host = os.environ.get("ROBOT_IP", "192.168.125.1")
    user = os.environ.get("RWS_USER", "Default User")
    password = os.environ.get("RWS_PASSWORD", "robotics")
    signal_name = os.environ.get("RWS_SIGNAL_NAME", "DO_EXAMPLE")

    print(f"Connecting to {host} ...")
    print(f"Target signal: {signal_name!r}")

    try:
        async with RWSClient(host=host, username=user, password=password) as client:
            # List all signals (overview)
            print("\nFetching signal list ...")
            resp_list = await get_io_signals(client)
            print(f"HTTP {resp_list.status_code} — {len(resp_list.text)} bytes")

            # Search for the specific signal by name
            print(f"\nSearching for signal {signal_name!r} ...")
            resp_search = await post_signal_search(
                client,
                action="signal-search",
                name=signal_name,
            )
            print(f"HTTP {resp_search.status_code}")

            current = _parse_lvalue(resp_search)
            print(f"Current value: {current!r}")

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
            #
            # Once rws/iosystem/signal.py is generated, replace the above
            # with the dedicated atomic function.

            print("\nDone.")

    except RWSError as exc:
        print(f"RWS error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
