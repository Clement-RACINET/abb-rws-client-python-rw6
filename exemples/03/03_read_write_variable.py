# exemples/03_read_write_variable.py
"""Example 03 — Read and write a RAPID variable.

Demonstrates:
    - Reading a RAPID VAR/PERS via get_variable (highlevel)
    - Writing a RAPID VAR/PERS via set_variable_with_mastership (highlevel)

Prerequisites:
    - Controller in AUTO mode
    - Module ExampleReadWrite loaded in T_ROB1 (see exemples/03_read_write.mod)
    - .env with ROBOT_IP, RWS_USER, RWS_PASSWORD

RAPID side: see exemples/03_read_write.mod

Run:
    pixi run python exemples/03_read_write_variable.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from _env import load_env

from abb_rws_client import RWSClient, RWSError
from abb_rws_client.highlevel.rapid import get_variable, set_variable_with_mastership


async def main() -> None:
    load_env()

    host = os.environ.get("ROBOT_IP", "192.168.125.1")
    user = os.environ.get("RWS_USER", "Default User")
    password = os.environ.get("RWS_PASSWORD", "robotics")

    task = os.environ.get("RWS_RAPID_TASK", "T_ROB1")
    module = "ExampleReadWrite"

    sym_counter = f"RAPID/{task}/{module}/gCounter"
    sym_message = f"RAPID/{task}/{module}/gMessage"
    sym_enabled = f"RAPID/{task}/{module}/gEnabled"

    print(f"Connecting to {host} ...")

    try:
        async with RWSClient(host=host, username=user, password=password) as client:
            print("\nReading current values ...")
            counter = await get_variable(client, symbolurl=sym_counter)
            message = await get_variable(client, symbolurl=sym_message)
            enabled = await get_variable(client, symbolurl=sym_enabled)

            print(f"  gCounter = {counter!r}")
            print(f"  gMessage = {message!r}")
            print(f"  gEnabled = {enabled!r}")

            new_counter = str(int(counter) + 1) if counter.isdigit() else "1"
            print(f"\nWriting gCounter = {new_counter} ...")
            await set_variable_with_mastership(
                client, symbolurl=sym_counter, value=new_counter
            )

            print('Writing gMessage = "Hello from Python" ...')
            await set_variable_with_mastership(
                client, symbolurl=sym_message, value='"Hello from Python"'
            )

            print("Writing gEnabled = TRUE ...")
            await set_variable_with_mastership(
                client, symbolurl=sym_enabled, value="TRUE"
            )

            print("\nVerifying ...")
            counter_after = await get_variable(client, symbolurl=sym_counter)
            message_after = await get_variable(client, symbolurl=sym_message)
            enabled_after = await get_variable(client, symbolurl=sym_enabled)

            print(f"  gCounter = {counter_after!r}  (was {counter!r})")
            print(f"  gMessage = {message_after!r}")
            print(f"  gEnabled = {enabled_after!r}")
            print("\nDone.")

    except RWSError as exc:
        print(f"RWS error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
