# exemples/02_start_stop.py
"""Example 02 — Start and stop RAPID execution.

Prerequisites:
    - Controller in AUTO mode, motors ON
    - A RAPID program loaded in T_ROB1 with a main() procedure
    - .env with ROBOT_IP, RWS_USER, RWS_PASSWORD

RAPID side: see exemples/02_start_stop.mod

Run:
    pixi run python exemples/02_start_stop.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from _env import load_env

from abb_rws_client import RWSClient, RWSError
from abb_rws_client.highlevel.rapid import (
    is_running,
    start_rapid,
    stop_rapid,
    wait_until_stopped,
)


async def main() -> None:
    load_env()

    host = os.environ.get("ROBOT_IP", "192.168.125.1")
    user = os.environ.get("RWS_USER", "Default User")
    password = os.environ.get("RWS_PASSWORD", "robotics")

    print(f"Connecting to {host} ...")

    try:
        async with RWSClient(host=host, username=user, password=password) as client:
            running = await is_running(client)
            print(f"Initial state: {'RUNNING' if running else 'STOPPED'}")

            if running:
                print("Already running — stopping first ...")
                await stop_rapid(client)
                await wait_until_stopped(client, timeout=10.0)
                print("Stopped.")

            print("Starting RAPID (cycle=once) ...")
            await start_rapid(client, cycle="once")
            print("Start command sent.")

            print("Waiting for program to finish ...")
            await wait_until_stopped(client, poll_interval=0.5, timeout=30.0)
            print("Program finished (state=stopped).")

    except TimeoutError:
        print("Timeout: program did not stop within the allowed time.", file=sys.stderr)
        sys.exit(1)
    except RWSError as exc:
        print(f"RWS error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
