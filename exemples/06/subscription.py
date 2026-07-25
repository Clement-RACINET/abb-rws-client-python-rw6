#!/usr/bin/env python3
# exemples/06/subscription.py
"""Example 06 — RWS WebSocket subscription on a RAPID PERS variable.

This example demonstrates how to subscribe to a RAPID persistent variable
through ABB Robot Web Services, then receive change events over WebSocket.

RAPID side
----------
The RAPID module used by this example contains:

    PERS num WatchedValue := 0;

The variable must be persistent, i.e. declared as ``PERS``. RWS subscriptions
on RAPID variable values are intended for persistent RAPID data.

ABB RWS subscription flow
-------------------------
1. Create the subscription with:

       POST /subscription

   Body:

       resources=1
       1=/rw/rapid/symbol/data/RAPID/T_ROB1/Subscription/WatchedValue;value
       1-p=1

2. ABB returns HTTP 201 with a WebSocket endpoint, typically:

       ws://<controller-host>:80/poll/<subscription_id>

3. The client opens the WebSocket using:
   - the same RWS session cookies;
   - the ABB subscription subprotocol:

         robapi2_subscription

   Important: do not use ``rws_subscription``. Some ABB RW6 controllers reject
   it with:

       Unsupported Sec-WebSocket-Protocol

4. Each time the watched variable changes, ABB sends an XML/XHTML event
   containing the new value, for example:

       <span class="value">1</span>

5. On shutdown, the script deletes the subscription with:

       DELETE /subscription/<subscription_id>

Notes for ABB RobotWare 6
-------------------------
- Use ``subprotocols=[Subprotocol("robapi2_subscription")]``.
- Use ``compression=None`` to avoid WebSocket permessage-deflate negotiation.
- Reuse the RWS HTTP cookies in the WebSocket handshake.
- The watched RAPID variable must be ``PERS``.
- This example auto-toggles the variable via RWS every few seconds, so no
  manual FlexPendant action is required.

Requirements
------------
- websockets >= 13.0
- An ABB RW6 controller with RWS enabled
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
import contextlib
import re
import signal
import time
from urllib.parse import urlparse, urlunparse

import websockets.asyncio.client
from websockets.typing import Subprotocol

from abb_rws_client_python_rw6 import configure_logging, load_env
from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.exceptions import RWSError
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.highlevel.variables import (
    get_variable,
    set_variable_with_mastership,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TASK: str = "T_ROB1"
MODULE: str = "Subscription"
VARIABLE: str = "WatchedValue"

# ABB subscription priority:
#   0 = high
#   1 = medium
#   2 = low
PRIORITY: str = "1"

# Demo helper:
# Python toggles the watched variable every N seconds so the WebSocket stream
# receives events without requiring manual RAPID calls from the FlexPendant.
TOGGLE_INTERVAL_S: float = 3.0

# ABB RW6 WebSocket subscription subprotocol.
#
# BasedPyright note:
# websockets expects Sequence[Subprotocol] | None, not a plain list[str].
# Therefore we explicitly wrap the protocol name with Subprotocol(...).
RWS_SUBPROTOCOLS: tuple[Subprotocol, ...] = (Subprotocol("robapi2_subscription"),)


# ---------------------------------------------------------------------------
# Subscription helpers
# ---------------------------------------------------------------------------


def build_symbolurl(task: str, module: str, variable: str) -> str:
    """Build a RAPID symbol URL.

    ABB RWS uses a symbol URL to identify RAPID data.

    Args:
        task: RAPID task name, for example ``"T_ROB1"``.
        module: RAPID module name, for example ``"Subscription"``.
        variable: RAPID variable name, for example ``"WatchedValue"``.

    Returns:
        Symbol URL suitable for RAPID symbol endpoints.

    Example:
        ``RAPID/T_ROB1/Subscription/WatchedValue``
    """
    return f"RAPID/{task}/{module}/{variable}"


def build_subscription_resource(task: str, module: str, variable: str) -> str:
    """Build the ABB RWS subscription resource URI.

    ABB expects subscription resources in this form:

        /rw/rapid/symbol/data/{symbolurl};value

    Args:
        task: RAPID task name.
        module: RAPID module name.
        variable: RAPID persistent variable name.

    Returns:
        RWS resource URI to use in ``POST /subscription``.

    Example:
        ``/rw/rapid/symbol/data/RAPID/T_ROB1/Subscription/WatchedValue;value``
    """
    symbolurl = build_symbolurl(task, module, variable)
    return f"/rw/rapid/symbol/data/{symbolurl};value"


def parse_subscription_response(
    html: str,
    headers: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Extract the WebSocket URL and subscription ID from ABB's response.

    Depending on controller / RobotWare version, ABB may return the WebSocket
    URL in:
    - the HTTP ``Location`` header;
    - the response body as an ``<a href="ws://...">`` link.

    Args:
        html: Raw response body from ``POST /subscription``.
        headers: Optional response headers.

    Returns:
        A tuple ``(ws_url, group_id)``:
        - ``ws_url``: WebSocket URL, for example
          ``ws://192.168.125.1:80/poll/43``.
        - ``group_id``: subscription ID, for example ``"43"``.

    Raises:
        ValueError: If no WebSocket URL or subscription ID can be extracted.
    """
    ws_url: str | None = None

    # 1. Try Location header first.
    if headers:
        for key, value in headers.items():
            if key.lower() == "location":
                candidate = value.strip()
                if candidate.startswith(("ws://", "wss://")):
                    ws_url = candidate
                    break

    # 2. Fallback: parse body with a broad href pattern.
    if ws_url is None:
        match = re.search(
            r'href=["\']([^"\']*(?:ws|wss)://[^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )
        if match:
            ws_url = match.group(1).strip()

    # 3. More explicit fallback for href="ws://...".
    if ws_url is None:
        match = re.search(
            r'href=["\'](ws://[^"\']+|wss://[^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )
        if match:
            ws_url = match.group(1).strip()

    if ws_url is None:
        raise ValueError(
            "Cannot find WebSocket URL in subscription response.\n"
            f"Headers: {headers}\n"
            f"Body first 500 chars:\n{html[:500]}"
        )

    id_match = re.search(r"/poll/([^/?#]+)", ws_url)
    if not id_match:
        raise ValueError(f"Cannot extract subscription ID from ws_url: {ws_url!r}")

    return ws_url, id_match.group(1)


def normalize_ws_url(ws_url: str, client: RWSClient) -> str:
    """Normalize ABB WebSocket URL.

    Some ABB examples and controller responses may contain localhost-style
    addresses such as:

        ws://127.0.0.1:9696/poll/N

    From a remote PC, ``127.0.0.1`` points to the PC itself, not to the robot.
    This helper replaces ``127.0.0.1`` or ``localhost`` by the actual
    controller host used by ``RWSClient``.

    Args:
        ws_url: Raw WebSocket URL returned by ABB.
        client: Active RWS client, used to retrieve the controller host.

    Returns:
        Normalized WebSocket URL.
    """
    parsed = urlparse(ws_url)

    hostname = parsed.hostname or client.host
    port = parsed.port

    if hostname in {"127.0.0.1", "localhost"}:
        hostname = client.host

    # Ruff SIM108: use a ternary expression instead of an if/else block.
    netloc = hostname if port is None else f"{hostname}:{port}"

    return urlunparse(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def parse_event_value(message: str) -> str | None:
    """Extract the new RAPID variable value from a WebSocket event.

    ABB sends XML/XHTML events such as:

        <span class="value">1</span>

    Args:
        message: Raw WebSocket message as text.

    Returns:
        Extracted value as a string, or ``None`` if the value cannot be found.
    """
    match = re.search(
        r'class=["\']value["\'][^>]*>([^<]+)<',
        message,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    return None


def build_cookie_header(client: RWSClient, response_headers: dict[str, str]) -> str:
    """Build the Cookie header for the WebSocket handshake.

    ABB RWS requires the WebSocket connection to reuse the same HTTP session
    cookies as the subscription request.

    This function collects cookies from:
    1. The underlying HTTP client's cookie jar.
    2. The ``Set-Cookie`` header from the subscription response as fallback.

    Args:
        client: Active RWS client.
        response_headers: Headers returned by ``POST /subscription``.

    Returns:
        Cookie header value, for example:

        ``-http-session-=...; ABBCX=...``
    """
    cookie_parts: list[str] = []

    # 1. Cookies already stored by the underlying httpx client.
    http_client = getattr(client, "_http", None)
    if http_client is not None:
        try:
            for cookie in http_client.cookies.jar:
                cookie_parts.append(f"{cookie.name}={cookie.value}")
        except Exception:
            # This is a fallback helper. If direct cookie-jar access fails,
            # the Set-Cookie header parsing below may still provide cookies.
            logger.debug("Could not read cookies from HTTP client jar.", exc_info=True)

    # 2. Fallback from Set-Cookie header.
    raw_set_cookie = ""
    for key, value in response_headers.items():
        if key.lower() == "set-cookie":
            raw_set_cookie = value
            break

    if raw_set_cookie:
        # ABB usually gives cookies like:
        #     -http-session-=...; path=/, ABBCX=...; path=/
        #
        # Splitting Set-Cookie on "," is not universally safe for all cookies,
        # but it works for ABB's simple session cookies used here.
        for segment in raw_set_cookie.split(","):
            kv = segment.strip().split(";")[0].strip()
            if "=" in kv:
                cookie_parts.append(kv)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    unique_parts: list[str] = []

    for part in cookie_parts:
        name = part.split("=", 1)[0]
        if name not in seen:
            seen.add(name)
            unique_parts.append(part)

    return "; ".join(unique_parts)


# ---------------------------------------------------------------------------
# RAPID variable toggle
# ---------------------------------------------------------------------------


async def toggle_loop(client: RWSClient, stop_event: asyncio.Event) -> None:
    """Toggle the watched RAPID variable every ``TOGGLE_INTERVAL_S`` seconds.

    This task exists only to make the example self-contained.

    Without this helper, you would need to manually call a RAPID procedure from
    the FlexPendant to modify ``WatchedValue`` and trigger subscription events.

    Args:
        client: Active RWS client.
        stop_event: Event used to stop the loop cleanly.
    """
    symbolurl = build_symbolurl(TASK, MODULE, VARIABLE)

    with contextlib.suppress(asyncio.CancelledError):
        while not stop_event.is_set():
            await asyncio.sleep(TOGGLE_INTERVAL_S)

            if stop_event.is_set():
                break

            try:
                current_raw = await get_variable(
                    client,
                    symbolurl=symbolurl,
                )

                current = int(float(current_raw))
                new_value = str(1 - (current % 2))

                await set_variable_with_mastership(
                    client,
                    symbolurl=symbolurl,
                    value=new_value,
                    domain="rapid",
                )

                logger.info("toggle: %s %s → %s", VARIABLE, current, new_value)
                print(
                    f"[toggle] {VARIABLE} {current} → {new_value}"
                    f" | time: {time.time() * 1000:.3f} ms"
                )

            except Exception as exc:
                logger.warning("toggle failed: %s", exc)


# ---------------------------------------------------------------------------
# Subscription generator
# ---------------------------------------------------------------------------


async def watch_rapid_variable(
    client: RWSClient,
    task: str,
    module: str,
    variable: str,
    *,
    priority: str = "1",
) -> AsyncGenerator[str, None]:
    """Subscribe to a RAPID PERS variable and yield its values on change.

    This function:
    1. Creates the RWS subscription.
    2. Extracts the WebSocket endpoint.
    3. Opens the WebSocket with ABB-compatible settings.
    4. Yields parsed values from incoming events.
    5. Deletes the subscription when leaving the generator.

    Args:
        client: Active RWS client.
        task: RAPID task name.
        module: RAPID module name.
        variable: RAPID persistent variable name.
        priority: ABB subscription priority:
            - ``"0"``: high
            - ``"1"``: medium
            - ``"2"``: low

    Yields:
        New variable values as strings.
    """
    resource = build_subscription_resource(task, module, variable)

    logger.info("Creating subscription on %s", resource)

    response = await client.post(
        "/subscription",
        data={
            "resources": "1",
            "1": resource,
            "1-p": priority,
        },
    )

    headers = dict(response.headers)
    ws_url_raw, group_id = parse_subscription_response(response.text, headers)
    ws_url = normalize_ws_url(ws_url_raw, client)
    cookie_header = build_cookie_header(client, headers)

    logger.info("Subscription created: id=%s", group_id)
    logger.info("WebSocket URL: %s", ws_url)

    if not cookie_header:
        logger.warning("No Cookie header found for WebSocket connection.")
    else:
        logger.debug("WebSocket Cookie: %s", cookie_header)

    try:
        # ABB RobotWare 6 WebSocket subscription notes:
        #
        # - The expected subprotocol is:
        #       robapi2_subscription
        #
        # - Do NOT use:
        #       rws_subscription
        #
        #   ABB may reject it with:
        #       Unsupported Sec-WebSocket-Protocol
        #
        # - compression=None disables permessage-deflate negotiation.
        #   This avoids sending:
        #       Sec-WebSocket-Extensions: permessage-deflate
        #
        #   Some ABB RW6 controllers reject that extension with HTTP 400.
        async with websockets.asyncio.client.connect(
            ws_url,
            additional_headers={
                "Cookie": cookie_header,
            },
            subprotocols=RWS_SUBPROTOCOLS,
            open_timeout=10.0,
            ping_interval=None,
            compression=None,
        ) as websocket:
            print(f"[watch] Connected to {ws_url}")
            print("[watch] Waiting for events...\n")

            async for message in websocket:
                text = str(message)
                logger.debug("WebSocket message: %s", text)

                value = parse_event_value(text)
                if value is not None:
                    yield value
                else:
                    logger.debug("Event received, but no value found.")

    finally:
        logger.info("Deleting subscription id=%s", group_id)

        try:
            await client.delete(f"/subscription/{group_id}")
            logger.info("Subscription id=%s deleted", group_id)
        except Exception as exc:
            logger.warning("Could not delete subscription id=%s: %s", group_id, exc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def watch_task(client: RWSClient, stop_event: asyncio.Event) -> None:
    """Consume WebSocket subscription events.

    Args:
        client: Active RWS client.
        stop_event: Event used to stop the example after an error or Ctrl+C.
    """
    try:
        async for value in watch_rapid_variable(
            client,
            TASK,
            MODULE,
            VARIABLE,
            priority=PRIORITY,
        ):
            print(f"[event] {VARIABLE} = {value} | time: {time.time() * 1000:.3f} ms")

            if stop_event.is_set():
                break

    except asyncio.CancelledError:
        pass

    except Exception as exc:
        logger.error("watch failed: %s", exc, exc_info=True)
        stop_event.set()


async def main() -> None:
    """Run the subscription example.

    The example starts two concurrent tasks:
    - one task watches the WebSocket subscription;
    - one task toggles the RAPID variable every few seconds.

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
            print(f"[main] Watching RAPID/{TASK}/{MODULE}/{VARIABLE}")
            print(f"[main] Auto-toggle every {TOGGLE_INTERVAL_S}s — Press Ctrl+C to stop.\n")

            watcher = asyncio.create_task(watch_task(client, stop_event))
            toggler = asyncio.create_task(toggle_loop(client, stop_event))

            await stop_event.wait()

            toggler.cancel()
            watcher.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(toggler, watcher)

    except RWSError as exc:
        logger.error("RWS error: %s", exc)

    finally:
        print("[main] Done.")


if __name__ == "__main__":
    asyncio.run(main())
