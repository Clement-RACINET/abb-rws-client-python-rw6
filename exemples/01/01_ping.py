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
import sys

from _env import load_env

from abb_rws_client import RWSClient, RWSConnectionError, RWSError
from abb_rws_client.rws.panel import get_controller_state, get_operation_mode


async def main() -> None:
    load_env()

    host = os.environ.get("ROBOT_IP", "192.168.125.1")
    user = os.environ.get("RWS_USER", "Default User")
    password = os.environ.get("RWS_PASSWORD", "robotics")

    print(f"Connecting to {host} as '{user}' ...")

    try:
        async with RWSClient(host=host, username=user, password=password) as client:
            resp_state = await get_controller_state(client)
            print(f"HTTP {resp_state.status_code} — Controller reachable")
            print(f"Controller state response:\n{resp_state.text[:300]}")

            resp_mode = await get_operation_mode(client)
            print(f"HTTP {resp_mode.status_code} — Operation mode response:")
            print(resp_mode.text[:300])

    except RWSConnectionError as exc:
        print(f"Cannot reach controller at {host}: {exc}", file=sys.stderr)
        sys.exit(1)
    except RWSError as exc:
        print(f"RWS error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
