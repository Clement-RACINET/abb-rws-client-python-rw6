# exemples/01_ping.py
"""Example 01 — Ping: verify connectivity and read controller state.

Prerequisites:
    - .env file at the repository root with ROBOT_IP, RWS_USER, RWS_PASSWORD
    - Controller reachable on the network

RAPID side: none required (read-only, no program needed).

Run:
    pixi run python exemples/01_ping.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

from _env import load_env
import httpx

from abb_rws_client import RWSClient, RWSConnectionError, RWSError
from abb_rws_client.rws.panel import get_controller_state, get_operation_mode


def _extract_class_value(response: httpx.Response, css_class: str) -> str:
    """Extract the ``title`` attribute of the first element with a given CSS class.

    ABB RWS RobotWare 6 returns XML/HTML by default.  State values are
    encoded as ``title`` attributes on ``<li>`` elements whose ``class``
    matches the resource name.

    Args:
        response: Raw HTTP response from a RWS panel endpoint.
        css_class: CSS class name to search for (e.g. ``"pnl-ctrlstate"``).

    Returns:
        The ``title`` value as a string, or ``"<not found>"`` if absent.
    """
    match = re.search(
        rf'class="{re.escape(css_class)}"[^>]*title="([^"]+)"',
        response.text,
    )
    if match:
        return match.group(1)
    # Fallback: value may be in element text
    match = re.search(
        rf'class="{re.escape(css_class)}"[^>]*>([^<]+)<',
        response.text,
    )
    if match:
        return match.group(1).strip()
    return "<not found>"


async def main() -> None:
    load_env()

    host = os.environ.get("ROBOT_IP", "192.168.125.1")
    user = os.environ.get("RWS_USER", "Default User")
    password = os.environ.get("RWS_PASSWORD", "robotics")

    print(f"Connecting to {host} as '{user}' ...")

    try:
        async with RWSClient(host=host, username=user, password=password) as client:
            # Controller state
            resp_state = await get_controller_state(client)
            ctrl_state = _extract_class_value(resp_state, "pnl-ctrlstate")
            print(f"HTTP {resp_state.status_code} — Controller reachable")
            print(f"  ctrlstate : {ctrl_state}")

            # Operation mode
            resp_mode = await get_operation_mode(client)
            op_mode = _extract_class_value(resp_mode, "pnl-opmode")
            print(f"HTTP {resp_mode.status_code} — Operation mode")
            print(f"  opmode    : {op_mode}")

            # Summary
            print()
            print("Summary")
            print("-------")
            print(f"  Host         : {host}")
            print(f"  ctrlstate    : {ctrl_state}")
            print(f"  opmode       : {op_mode}")

    except RWSConnectionError as exc:
        print(f"Cannot reach controller at {host}: {exc}", file=sys.stderr)
        sys.exit(1)
    except RWSError as exc:
        print(f"RWS error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
