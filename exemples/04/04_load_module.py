# exemples/04_load_module.py
"""Example 04 — Load a RAPID module into a task at runtime.

Demonstrates:
    - Using load_module_safe (highlevel) to unload/load with mastership

Prerequisites:
    - Controller in AUTO mode, RAPID stopped
    - Module file already present on the controller at CONTROLLER_PATH
      (upload it beforehand via FTP, USB, or RWS fileservice)
    - .env with ROBOT_IP, RWS_USER, RWS_PASSWORD, RWS_RAPID_TASK

RAPID side: see exemples/04_load_module.mod

Run:
    pixi run python exemples/04_load_module.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from _env import load_env

from abb_rws_client import RWSClient, RWSError
from abb_rws_client.highlevel.rapid import is_running, load_module_safe, stop_rapid


async def main() -> None:
    load_env()

    host = os.environ.get("ROBOT_IP", "192.168.125.1")
    user = os.environ.get("RWS_USER", "Default User")
    password = os.environ.get("RWS_PASSWORD", "robotics")

    task = os.environ.get("RWS_RAPID_TASK", "T_ROB1")
    module_name = "ExampleLoadModule"
    # Path on the controller filesystem.
    # The file must be uploaded beforehand (via FTP, USB, or RWS fileservice).
    controller_path = f"$HOME/{module_name}.mod"

    print(f"Connecting to {host} ...")
    print(f"Module      : {module_name}")
    print(f"Controller  : {controller_path}")
    print(f"Task        : {task}")

    try:
        async with RWSClient(host=host, username=user, password=password) as client:
            if await is_running(client):
                print("RAPID is running — stopping before load ...")
                await stop_rapid(client)
                print("RAPID stopped.")

            print(f"\nLoading {module_name} into {task} ...")
            await load_module_safe(
                client,
                task=task,
                module_name=module_name,
                module_path=controller_path,
            )
            print(f"Module '{module_name}' loaded successfully into {task}.")
            print("\nYou can now run example 02 to execute it.")

    except RWSError as exc:
        print(f"RWS error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
