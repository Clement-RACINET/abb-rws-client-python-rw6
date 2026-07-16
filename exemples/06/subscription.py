#!/usr/bin/env python3
# exemples/06/subscription.py
"""Example 06 — RWS WebSocket subscription on a RAPID PERS variable.

Author: Clement RACINET

Demonstrates how to subscribe to a RAPID PERS variable via ABB RWS
and receive change events over WebSocket, without polling.

Protocol (ABB RWS RobotWare 6):
    1. POST /subscription  → HTTP 201 + Location: ws://<host>/poll/<id>
    2. Connect WebSocket   → robot pushes XML events on each value change
    3. DELETE /subscription/<id>  → clean unsubscribe

Requirements (pixi env: examples):
    httpx-ws >= 0.6

Usage:
    pixi run -e examples example-06

    On the FlexPendant, run ToggleWatchedValue repeatedly
    to see events arrive.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
import contextlib
import re
import signal

import httpx_ws  # type: ignore[import-untyped]

from abb_rws_client_python_rw6 import RWSClient, configure_logging, load_env
from abb_rws_client_python_rw6.rws.rapid.symbol import (
    subscribe_on_rapid_persistent_variable,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TASK: str = "T_ROB1"
MODULE: str = "ExampleSubscription"
VARIABLE: str = "WatchedValue"
PRIORITY: str = "1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_resource_url(task: str, module: str, variable: str) -> str:
    """Build the RWS resource URL for a RAPID PERS variable subscription.

    Args:
        task: RAPID task name (e.g. ``"T_ROB1"``).
        module: RAPID module name (e.g. ``"ExampleSubscription"``).
        variable: RAPID variable name (e.g. ``"WatchedValue"``).

    Returns:
        Resource URL string for use in the subscription body,
        e.g. ``"/rw/rapid/symbol/data/RAPID/T_ROB1/M/x;value"``.

    Example:
        ::

            url = _build_resource_url("T_ROB1", "M", "x")
            # → "/rw/rapid/symbol/data/RAPID/T_ROB1/M/x;value"
    """
    return f"/rw/rapid/symbol/data/RAPID/{task}/{module}/{variable};value"


def _extract_group_id(location: str) -> str:
    """Extract the subscription group ID from the Location header.

    ABB RWS returns a Location header like:
        ``http://192.168.125.1/subscription/1``

    Args:
        location: Value of the ``Location`` header from the HTTP 201 response.

    Returns:
        The group ID string (last path segment).

    Raises:
        ValueError: If the group ID cannot be extracted.

    Example:
        ::

            _extract_group_id("http://192.168.125.1/subscription/42")
            # → "42"
    """
    match = re.search(r"/(\w+)$", location.rstrip("/"))
    if not match:
        raise ValueError(f"Cannot extract group ID from Location: {location!r}")
    return match.group(1)


def _extract_ws_url(location: str, host: str, port: int) -> str:
    """Build the WebSocket URL from the Location header.

    ABB may return either an ``http://`` or ``ws://`` URL in the
    Location header. This function normalises it to ``ws://``.

    Args:
        location: Value of the ``Location`` header.
        host: Controller hostname/IP (used as fallback if Location
            contains a relative path).
        port: Controller HTTP port.

    Returns:
        WebSocket URL string, e.g. ``"ws://192.168.125.1/poll/42"``.

    Example:
        ::

            _extract_ws_url("http://192.168.125.1/poll/42", "192.168.125.1", 80)
            # → "ws://192.168.125.1/poll/42"
    """
    ws_url = re.sub(r"^https?://", "ws://", location)
    if ws_url.startswith("/"):
        ws_url = f"ws://{host}:{port}{ws_url}"
    return ws_url


def _parse_event_value(message: str) -> str | None:
    """Extract the variable value from an ABB RWS subscription event.

    ABB sends XML/HTML events like::

        <li class="rapid-symbol-data-ev">
          <span class="lvalue">/rw/rapid/symbol/data/RAPID/T_ROB1/M/x</span>
          <span class="value">42</span>
        </li>

    Args:
        message: Raw WebSocket message string (XML/HTML).

    Returns:
        The new value as a string, or ``None`` if not parseable.

    Example:
        ::

            _parse_event_value('<span class="value">42</span>')
            # → "42"
    """
    match = re.search(r'class=["\']value["\'][^>]*>([^<]+)<', message)
    if match:
        return match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Core subscription generator
# ---------------------------------------------------------------------------


async def watch_rapid_variable(
    client: RWSClient,
    task: str,
    module: str,
    variable: str,
    *,
    priority: str = "1",
) -> AsyncGenerator[str, None]:
    """Subscribe to a RAPID PERS variable and yield new values on change.

    Opens a WebSocket subscription on the ABB controller and yields
    the new value as a string each time the variable changes.

    The subscription is automatically cleaned up (DELETE) when the
    generator is closed, even on cancellation.

    Route:
        - ``POST /subscription`` → HTTP 201 + Location header
        - WebSocket on Location URL (``receive_text()`` loop)
        - ``DELETE /subscription/{group_id}`` on exit

    ABB constraints:
        - Variable must be declared ``PERS`` in the RAPID module.
        - Not supported in bootserver mode.
        - Maximum 1000 resources per subscription group.
        - Maximum 2 groups per client session.
        - Priority 2 (high) limited to 64 resources per client.

    Args:
        client: Open :class:`~abb_rws_client_python_rw6.RWSClient` instance.
        task: RAPID task name (e.g. ``"T_ROB1"``).
        module: RAPID module name containing the variable.
        variable: RAPID variable name (must be ``PERS``).
        priority: Subscription priority. ``"0"``=low, ``"1"``=medium,
            ``"2"``=high. Defaults to ``"1"``.

    Yields:
        New value of the variable as a string on each change event.

    Raises:
        RWSHTTPError: If the subscription POST fails.
        ValueError: If the Location header is missing or malformed.

    Example:
        ::

            async with RWSClient(host="192.168.125.1") as client:
                async for value in watch_rapid_variable(
                    client, "T_ROB1", "ExampleSubscription", "WatchedValue"
                ):
                    print(f"New value: {value}")
    """
    resource_url = _build_resource_url(task, module, variable)

    # ── Step 1 : POST /subscription ───────────────────────────────────────
    response = await subscribe_on_rapid_persistent_variable(
        client,
        identifier=resource_url,
        identifier_p=priority,
    )

    location = response.headers.get("Location", "")
    if not location:
        raise ValueError(
            f"ABB RWS did not return a Location header. "
            f"Response status: {response.status_code}, "
            f"body: {response.text[:200]}"
        )

    group_id = _extract_group_id(location)
    ws_url = _extract_ws_url(location, client.host, client.port)

    print(f"[subscription] group_id={group_id!r}  ws_url={ws_url!r}")

    assert client._http is not None, "RWSClient must be open"  # noqa: S101

    try:
        # ── Step 2 : WebSocket receive loop ───────────────────────────────
        # httpx_ws.aconnect_ws reuses the httpx.AsyncClient session,
        # so the ABBCX cookie is forwarded automatically.
        async with httpx_ws.aconnect_ws(ws_url, client._http) as ws:
            print(f"[subscription] WebSocket connected → {ws_url}")
            while True:
                try:
                    message = await ws.receive_text()   # blocks until event
                    value = _parse_event_value(message)
                    if value is not None:
                        yield value
                except httpx_ws.WebSocketDisconnect:
                    print("[subscription] WebSocket disconnected by server.")
                    break
    finally:
        # ── Step 3 : DELETE /subscription/{group_id} ──────────────────────
        with contextlib.suppress(Exception):
            await client.delete(f"/subscription/{group_id}")
            print(f"[subscription] Unsubscribed group {group_id!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the subscription example.

    Connects to the controller, subscribes to ``WatchedValue``, and
    prints each new value until Ctrl+C is pressed.
    """
    load_env()
    configure_logging("DEBUG")

    stop_event = asyncio.Event()

    def _on_sigint(*_: object) -> None:
        print("\n[main] Ctrl+C — stopping…")
        stop_event.set()

    signal.signal(signal.SIGINT, _on_sigint)

    async with RWSClient() as client:
        print(f"[main] Connected to {client.host}:{client.port}")
        print(f"[main] Watching RAPID/{TASK}/{MODULE}/{VARIABLE}")
        print("[main] Run ToggleWatchedValue on the FlexPendant.")
        print("[main] Press Ctrl+C to stop.\n")

        watch_task = asyncio.create_task(_watch(client, stop_event))
        await stop_event.wait()
        watch_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await watch_task

    print("[main] Done.")


async def _watch(client: RWSClient, stop_event: asyncio.Event) -> None:
    """Consume the subscription generator until stop is requested.

    Args:
        client: Open RWSClient instance.
        stop_event: Event set when the user requests shutdown.
    """
    with contextlib.suppress(asyncio.CancelledError):
        async for value in watch_rapid_variable(
            client, TASK, MODULE, VARIABLE, priority=PRIORITY
        ):
            print(f"  → {VARIABLE} = {value}")
            if stop_event.is_set():
                break


if __name__ == "__main__":
    asyncio.run(main())
