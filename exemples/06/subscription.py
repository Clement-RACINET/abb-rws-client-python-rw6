#!/usr/bin/env python3
# examples/06/subscription.py
"""Example 06 — RWS WebSocket subscription on two RAPID PERS variables.

Author: Clement RACINET

Demonstrates the high-level subscription API (highlevel/subscription.py):
subscribing to several RAPID persistent variables at once, at different ABB
priorities, and consuming their change events as plain (name, value) tuples.

RAPID side
----------
The RAPID module used by this example (examples/06/Subscription.mod)
declares:

    PERS num WatchedValue1 := 0;
    PERS num WatchedValue2 := 0;

and cycles both automatically and forever from ``main()`` as soon as the
program is started (PP to Main + Start on the FlexPendant). No manual
routine call is needed: this Python script only watches, it never writes
to the controller.

ABB RWS subscription flow (see highlevel/subscription.py for the full
mechanics: POST /subscription, WebSocket handshake with the
``robapi2_subscription`` subprotocol, DELETE /subscription/{group-id} on
teardown).

Real-hardware validation note
------------------------------
This example subscribes to 2 resources in a single POST /subscription call.
The multi-resource payload format (N >= 2) used by
``highlevel.subscription.create_subscription`` is currently unverified on
real hardware (see the TODO in that module) — running this example against
a real RW6 controller is the intended way to confirm it works, or to reveal
what needs fixing.

Requirements
------------
- websockets >= 13.0
- An ABB RW6 controller with RWS enabled, running examples/06/Subscription.mod
"""

from __future__ import annotations

import asyncio
import contextlib
import signal

from abb_rws_client_python_rw6 import configure_logging, load_env
from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.exceptions import RWSError
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.highlevel.subscription import (
    SubscribedResource,
    build_rapid_pers_resource_uri,
    watch_resources,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TASK: str = "T_ROB1"
MODULE: str = "Subscription"

#: Two resources at different ABB priorities, to exercise the multi-resource
#: subscription payload (N=2) and show how priority affects delivery delay:
#: "1"=Medium (<=200ms), "2"=High (as soon as possible, PERS/IO only).
RESOURCES: list[SubscribedResource] = [
    SubscribedResource(
        name="value1",
        resource_uri=build_rapid_pers_resource_uri(TASK, MODULE, "WatchedValue1"),
        priority="1",
    ),
    SubscribedResource(
        name="value2",
        resource_uri=build_rapid_pers_resource_uri(TASK, MODULE, "WatchedValue2"),
        priority="2",
    ),
]


# ---------------------------------------------------------------------------
# Watch task
# ---------------------------------------------------------------------------


async def watch_task(client: RWSClient) -> None:
    """Subscribe to RESOURCES and print each incoming event.

    Uses ``contextlib.aclosing`` around ``watch_resources``: this guarantees
    the ABB subscription group is deleted (via the generator's internal
    ``finally``) even when this task is cancelled by Ctrl+C. A bare
    ``async for`` without ``aclosing`` would NOT close the generator on
    cancellation — cleanup would then only happen non-deterministically on
    garbage collection, leaking one of the controller's 2 allowed
    subscription groups per client.

    Args:
        client: Active RWS client.
    """
    async with contextlib.aclosing(watch_resources(client, RESOURCES)) as events:
        async for name, value in events:
            print(f"[event] {name} = {value}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the subscription example.

    Watches WatchedValue1 and WatchedValue2 as they are cycled automatically
    by the RAPID program (see examples/06/Subscription.mod). Python never
    writes to the controller here — it only subscribes and observes.

    Stop with Ctrl+C.
    """
    load_env()

    # Use "INFO" for normal demo output.
    # Use "DEBUG" if you want to inspect the raw XML WebSocket events.
    configure_logging("INFO")

    stop_event = asyncio.Event()

    def on_sigint(*_: object) -> None:
        print("\n[main] Ctrl+C — stopping…")
        stop_event.set()

    signal.signal(signal.SIGINT, on_sigint)

    try:
        async with RWSClient() as client:
            print(f"[main] Connected to {client.host}:{client.port}")
            print(f"[main] Watching {[r.name for r in RESOURCES]}")
            print("[main] Start RAPID execution (PP to Main + Start) if not already running.")
            print("[main] Press Ctrl+C to stop.\n")

            watcher = asyncio.create_task(watch_task(client))

            await stop_event.wait()

            watcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher

    except RWSError as exc:
        logger.error("RWS error: %s", exc)

    finally:
        print("[main] Done.")


if __name__ == "__main__":
    asyncio.run(main())
