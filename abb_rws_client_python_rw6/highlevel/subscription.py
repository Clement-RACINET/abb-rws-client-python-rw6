# abb_rws_client_python_rw6/highlevel/subscription.py
"""High-level RWS subscription management for ABB RobotWare 6.

Author: Clement RACINET

Wraps the ABB RWS Subscription Service and the WebSocket event stream behind
a resource-oriented API: the caller declares a list of `SubscribedResource`
(name + RWS resource URI + ABB priority), and gets back logical
`(name, value)` events instead of raw XML.

ABB RWS subscription flow confirmed on real RW6 hardware:
    1. POST /subscription with a form-urlencoded body. For multiple
       resources, ABB expects the ``resources`` key to be repeated once per
       subscribed resource:
           resources=1
           1=<resource-uri>
           1-p=<priority>
           resources=2
           2=<resource-uri>
           2-p=<priority>
       Response: HTTP 201, body = initial events for each resource, plus a
       ``Location`` header = the WebSocket URL (``ws://host:port/poll/<id>``).
    2. Open a WebSocket on that URL, subprotocol ``robapi2_subscription``,
       reusing the RWS session cookies (``-http-session-``, ``ABBCX``).
    3. Each subscribed-resource change is pushed as an XML/XHTML event.
    4. Close the WebSocket to tear down the subscription group. If the
       WebSocket was never opened, DELETE /subscription/{group-id} can be
       used as fallback cleanup.

ABB priority semantics confirmed from ABB doc "Subscriptions":
    "0" = Low    (events sent with a maximum delay of 5 seconds)
    "1" = Medium (events sent with a maximum delay of 200 ms)
    "2" = High   (events sent as soon as they occur; applicable only to
                  persistent RAPID variables and IO signals; limit of 64
                  high-priority subscribed resources)

ABB subscription limits confirmed from ABB doc "Subscriptions":
    - Maximum of 1000 unique low/medium-priority resources for all clients.
    - Maximum of 64 high-priority resources.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
import re
from typing import Literal
from urllib.parse import urlencode, urlparse, urlunparse

import websockets.asyncio.client
from websockets.typing import Subprotocol

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: ABB subscription priority. Confirmed by ABB doc: "0"=Low, "1"=Medium,
#: "2"=High (PERS RAPID variables and IO signals only, max 64 resources).
SubscriptionPriority = Literal["0", "1", "2"]

#: ABB RW6 WebSocket subscription subprotocol (confirmed by ABB doc,
#: confirmed working on real hardware in examples/06). Do NOT use
#: "rws_subscription": some RW6 controllers reject it with
#: "Unsupported Sec-WebSocket-Protocol".
_RWS_SUBPROTOCOLS: tuple[Subprotocol, ...] = (Subprotocol("robapi2_subscription"),)

#: Prefix stripped to recover a bare RAPID symbolurl (e.g.
#: "RAPID/T_ROB1/MOD/VAR") from a full resource URI (e.g.
#: "/rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR;value"). ABB uses the bare
#: form in the "title" attribute of "rap-data" <li> elements.
_SYMBOL_DATA_PREFIX = "/rw/rapid/symbol/data/"

#: ABB hard limits, confirmed by ABB doc "Subscriptions".
_MAX_RESOURCES_TOTAL = 1000
_MAX_HIGH_PRIORITY_RESOURCES = 64

# XML parsing patterns. ABB events are XHTML fragments, not well-formed
# enough to justify a full XML parser dependency; the structure is stable
# and documented (title/href/span attributes).
_LI_BLOCK_RE = re.compile(r"<li\b[^>]*>.*?</li>", re.IGNORECASE | re.DOTALL)
_TITLE_RE = re.compile(r'title=["\']([^"\']*)["\']', re.IGNORECASE)
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_VALUE_SPAN_RE = re.compile(
    r'<span[^>]*class=["\'][^"\']*value[^"\']*["\'][^>]*>([^<]*)</span>',
    re.IGNORECASE,
)
_WS_HREF_RE = re.compile(r'href=["\'](wss?://[^"\']+)["\']', re.IGNORECASE)
_GROUP_ID_RE = re.compile(r"/poll/([^/?#]+)")


# ---------------------------------------------------------------------------
# Public data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubscribedResource:
    """One RWS resource to watch within a subscription group.

    Args:
        name: Caller-chosen logical identifier for this resource. Used only
            client-side to route incoming events back to the caller; never
            sent to ABB.
        resource_uri: Full ABB RWS resource URI to subscribe on, e.g.
            ``/rw/rapid/symbol/data/RAPID/T_ROB1/MOD/VAR;value``.
        priority: ABB subscription priority. ``"0"``=Low, ``"1"``=Medium,
            ``"2"``=High (PERS RAPID variables and IO signals only).

    Example:
        ```python
        >>> SubscribedResource(
        ...     name="watched_value",
        ...     resource_uri="/rw/rapid/symbol/data/RAPID/T_ROB1/Subscription/WatchedValue;value",
        ...     priority="1",
        ... )
        ```
    """

    name: str
    resource_uri: str
    priority: SubscriptionPriority = "1"


@dataclass(frozen=True)
class SubscriptionHandle:
    """Result of a successfully created ABB RWS subscription group.

    Args:
        group_id: ABB subscription group identifier (from the WebSocket
            URL path, e.g. ``"9"`` in ``ws://host/poll/9``).
        ws_url: WebSocket URL to open for this subscription group,
            normalized so that ``127.0.0.1``/``localhost`` (as sometimes
            returned by ABB) is replaced by the actual controller host.
        cookie_header: Session cookie header to send during the WebSocket
            handshake (``-http-session-=...; ABBCX=...``).
        resources: The resources this group was created with, kept to
            resolve incoming events back to their logical ``name``.
        initial_values: Values returned by ABB in the ``POST /subscription``
            response body itself (one entry per resource whose initial
            state ABB included), keyed by ``SubscribedResource.name``.
    """

    group_id: str
    ws_url: str
    cookie_header: str
    resources: tuple[SubscribedResource, ...]
    initial_values: dict[str, str]


def build_rapid_pers_resource_uri(task: str, module: str, variable: str) -> str:
    """Build the ABB RWS subscription resource URI for a RAPID PERS variable.

    Route: N/A — local string helper, no HTTP call performed.

    ABB constraints: The variable must be declared ``PERS`` in RAPID.
        Subscriptions on non-persistent (``VAR``) data are not supported by
        ABB (confirmed by ABB doc: "Subscribe on RAPID persistent variable").

    Args:
        task: RAPID task name, e.g. ``"T_ROB1"``.
        module: RAPID module name, e.g. ``"Subscription"``.
        variable: RAPID PERS variable name, e.g. ``"WatchedValue"``.

    Returns:
        Resource URI suitable for ``SubscribedResource.resource_uri``.

    Example:
        ```python
        >>> build_rapid_pers_resource_uri("T_ROB1", "Subscription", "WatchedValue")
        '/rw/rapid/symbol/data/RAPID/T_ROB1/Subscription/WatchedValue;value'
        ```
    """
    return f"{_SYMBOL_DATA_PREFIX}RAPID/{task}/{module}/{variable};value"


# ---------------------------------------------------------------------------
# Private helpers — payload / response parsing
# ---------------------------------------------------------------------------


def _validate_resources(resources: Sequence[SubscribedResource]) -> None:
    """Validate a resource list against ABB's documented hard limits.

    Args:
        resources: Resources about to be subscribed.

    Raises:
        ValueError: If the list is empty, exceeds 1000 total resources, or
            exceeds 64 High-priority ("2") resources (both limits confirmed
            by ABB doc "Subscriptions").
    """
    if not resources:
        raise ValueError("resources must contain at least one SubscribedResource")

    if len(resources) > _MAX_RESOURCES_TOTAL:
        raise ValueError(
            f"ABB allows at most {_MAX_RESOURCES_TOTAL} subscribed resources "
            f"(low/medium priority); got {len(resources)}"
        )

    high_count = sum(1 for r in resources if r.priority == "2")
    if high_count > _MAX_HIGH_PRIORITY_RESOURCES:
        raise ValueError(
            f"ABB allows at most {_MAX_HIGH_PRIORITY_RESOURCES} High-priority "
            f"('2') resources; got {high_count}"
        )


def _build_subscription_payload(resources: Sequence[SubscribedResource]) -> str:
    """Build the ABB RWS form-urlencoded payload for ``POST /subscription``.

    Route: ``POST /subscription``

    ABB constraints: ABB RW6 expects one ``resources=<identifier>`` entry per
        subscribed resource. The ``resources`` field declares the identifier
        used by the matching ``<identifier>`` and ``<identifier>-p`` fields.
        This repeated-key format was confirmed on real RW6 hardware with
        multiple RAPID PERS variables.

    Args:
        resources: Resources to subscribe to, in order.

    Returns:
        URL-encoded form body with repeated ``resources`` keys.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> _build_subscription_payload([
        ...     SubscribedResource(
        ...         "a",
        ...         "/rw/rapid/symbol/data/RAPID/T_ROB1/M/A;value",
        ...         "1",
        ...     ),
        ...     SubscribedResource(
        ...         "b",
        ...         "/rw/rapid/symbol/data/RAPID/T_ROB1/M/B;value",
        ...         "2",
        ...     ),
        ... ])
        'resources=1&1=...&1-p=1&resources=2&2=...&2-p=2'
        ```
    """

    pairs: list[tuple[str, str]] = []

    for index, resource in enumerate(resources, start=1):
        identifier = str(index)
        pairs.append(("resources", identifier))
        pairs.append((identifier, resource.resource_uri))
        pairs.append((f"{identifier}-p", resource.priority))

    return urlencode(pairs)


def _build_resource_lookup(resources: Sequence[SubscribedResource]) -> dict[str, str]:
    """Build a URI-to-name lookup table to resolve incoming ABB events.

    ABB identifies the changed resource either by:
    - the full resource URI in an ``<a href="...">`` (e.g. IO signal events,
      or the "rap-value-ev" link for RAPID PERS variables), or
    - the bare RAPID symbolurl in a ``title="..."`` attribute (the "rap-data"
      sibling <li>, confirmed by ABB doc "Subscribe on RAPID persistent
      variable" sample response).

    Args:
        resources: Resources this subscription group was created with.

    Returns:
        Dict mapping both the full ``resource_uri`` and (for RAPID symbol
        resources) the bare symbolurl to the caller's logical ``name``.
    """
    lookup: dict[str, str] = {}
    for resource in resources:
        lookup[resource.resource_uri] = resource.name
        if resource.resource_uri.startswith(_SYMBOL_DATA_PREFIX):
            # ABB's "rap-data" <li> uses the bare symbolurl (no ";value"
            # suffix, no "/rw/rapid/symbol/data/" prefix) in its "title"
            # attribute — register that alternate identity too.
            symbolurl = resource.resource_uri[len(_SYMBOL_DATA_PREFIX) :].split(";")[0]
            lookup[symbolurl] = resource.name
    return lookup


def _extract_li_blocks(text: str) -> list[str]:
    """Split an ABB XHTML fragment into its top-level ``<li>...</li>`` blocks.

    Args:
        text: Raw XHTML fragment (POST response body or WebSocket message).

    Returns:
        List of ``<li>`` blocks in document order, as raw strings.
    """
    return _LI_BLOCK_RE.findall(text)


def _extract_resource_identity(block: str) -> str | None:
    """Extract the resource identity carried by one ``<li>`` block, if any.

    ABB carries resource identity in one of two ways (both confirmed by ABB
    doc samples):
    - ``<a href="{resource-uri}" .../>`` — the full subscribed URI, matches
      ``SubscribedResource.resource_uri`` directly.
    - ``title="{symbolurl}"`` on a RAPID "rap-data" block — matches the bare
      symbolurl form registered by ``_build_resource_lookup``. A generic
      title with no ``/`` (e.g. ``title="value"`` on "rap-value-ev" blocks)
      carries no resource identity and is ignored.

    Args:
        block: One ``<li>...</li>`` XHTML block.

    Returns:
        The extracted identity string, or ``None`` if this block carries
        no resolvable resource identity.
    """
    href_match = _HREF_RE.search(block)
    if href_match:
        return href_match.group(1)

    title_match = _TITLE_RE.search(block)
    if title_match and "/" in title_match.group(1):
        return title_match.group(1)

    return None


def _extract_value(block: str) -> str | None:
    """Extract the value carried by one ``<li>`` block, if any.

    Matches ``<span class="...value...">...</span>``, covering both
    ``class="value"`` (RAPID events) and ``class="lvalue"`` (IO signal
    events) — both documented by ABB.

    Args:
        block: One ``<li>...</li>`` XHTML block.

    Returns:
        The extracted value as a string, or ``None`` if this block carries
        no value span.
    """
    value_match = _VALUE_SPAN_RE.search(block)
    return value_match.group(1).strip() if value_match else None


def _parse_events(text: str, lookup: dict[str, str]) -> dict[str, str]:
    """Parse ABB subscription events into ``{name: value}``.

    Handles both documented ABB XML shapes:
    - Single-block events, where identity and value are in the same
      ``<li>`` (generic IO signal example in ABB doc).
    - Split-block events, where an "-ev" ``<li>`` carries only the
      identity (``href``) and the immediately following ``<li>`` carries
      only the value (the "rap-data" block, confirmed by ABB doc "Subscribe
      on RAPID persistent variable" sample response).

    Args:
        text: Raw XHTML fragment (POST response body or WebSocket message).
        lookup: Resource-identity-to-name table from ``_build_resource_lookup``.

    Returns:
        Dict of ``{SubscribedResource.name: value}`` for every resolvable
        event found in ``text``. Events for resources not present in
        ``lookup`` are silently ignored (logged at DEBUG level) — this
        happens if ABB pushes an event for a resource outside this group.
    """
    events: dict[str, str] = {}
    pending_identity: str | None = None

    for block in _extract_li_blocks(text):
        identity = _extract_resource_identity(block)
        value = _extract_value(block)

        if identity is not None:
            pending_identity = identity

        if value is None:
            continue

        resolved_identity = identity if identity is not None else pending_identity
        if resolved_identity is None:
            logger.debug("Value span with no resolvable resource identity: %r", block)
            continue

        name = lookup.get(resolved_identity)
        if name is None:
            logger.debug("Event for unsubscribed resource %r ignored", resolved_identity)
            continue

        events[name] = value
        pending_identity = None  # Consumed — avoid leaking into next block.

    return events


def _extract_ws_url_and_group_id(response_text: str, headers: dict[str, str]) -> tuple[str, str]:
    """Extract the WebSocket URL and group id from ABB's subscription response.

    ABB constraints: The WebSocket URL is normally in the ``Location``
        header; some controllers only expose it as an
        ``<a href="ws://...">`` link in the response body.

    Args:
        response_text: Raw ``POST /subscription`` response body.
        headers: Response headers (case preserved, matched case-insensitively).

    Returns:
        ``(ws_url, group_id)``, e.g. ``("ws://host:80/poll/9", "9")``.

    Raises:
        ValueError: If no WebSocket URL, or no group id within it, can be found.
    """
    ws_url: str | None = None

    for key, value in headers.items():
        if key.lower() == "location":
            candidate = value.strip()
            if candidate.startswith(("ws://", "wss://")):
                ws_url = candidate
                break

    if ws_url is None:
        match = _WS_HREF_RE.search(response_text)
        if match:
            ws_url = match.group(1).strip()

    if ws_url is None:
        raise ValueError(
            "Could not extract WebSocket URL from ABB subscription response "
            f"(headers={headers!r}, body[:500]={response_text[:500]!r})"
        )

    group_id_match = _GROUP_ID_RE.search(ws_url)
    if not group_id_match:
        raise ValueError(f"Could not extract subscription group id from ws_url={ws_url!r}")

    return ws_url, group_id_match.group(1)


def _normalize_ws_url(ws_url: str, client: RWSClient) -> str:
    """Replace a loopback host in an ABB WebSocket URL by the real controller host.

    ABB constraints: Some RW6 controllers return ``ws://127.0.0.1:9696/...``
        (loopback from the controller's own point of view). From a remote
        client, ``127.0.0.1`` points to the client itself, not the robot.

    Args:
        ws_url: Raw WebSocket URL returned by ABB.
        client: Active RWS client, used to recover the real controller host.

    Returns:
        Normalized WebSocket URL, unchanged if the host was not a loopback
        address.
    """
    parsed = urlparse(ws_url)
    hostname = parsed.hostname or client.host
    port = parsed.port

    if hostname in {"127.0.0.1", "localhost"}:
        hostname = client.host

    netloc = hostname if port is None else f"{hostname}:{port}"

    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def create_subscription(
    client: RWSClient,
    resources: Sequence[SubscribedResource],
) -> SubscriptionHandle:
    """Create an ABB RWS subscription group for one or more resources.

    Route: ``POST /subscription``

    ABB constraints:
        - Max 1000 total resources per client for low/medium priority.
        - Max 64 resources at High priority ``"2"``.
        - Max 2 subscription groups per client.
        - The multi-resource form body must repeat the ``resources`` key once
          per subscribed resource.
        - The response body contains the initial event state for the
          subscribed resources.
        - The ``Location`` header carries the WebSocket URL.
        - The WebSocket handshake must reuse the session cookies captured
          after the subscription creation response.

    Args:
        client: Open RWSClient instance.
        resources: Resources to subscribe to.

    Returns:
        SubscriptionHandle with the group id, normalized WebSocket URL,
        session cookie header, subscribed resources and initial values.

    Raises:
        ValueError: If the resource list is invalid or the ABB response cannot
            be parsed.
        RWSAuthenticationError: On HTTP 401.
        RWSHTTPError: On any other HTTP status greater than or equal to 400.

    Example:
        ```python
        >>> handle = await create_subscription(
        ...     client,
        ...     [
        ...         SubscribedResource(
        ...             "watched",
        ...             "/rw/rapid/symbol/data/RAPID/T_ROB1/M/x;value",
        ...             "1",
        ...         )
        ...     ],
        ... )
        ```
    """

    _validate_resources(resources)

    payload = _build_subscription_payload(resources)
    lookup = _build_resource_lookup(resources)

    logger.info("Creating subscription on %d resource(s)", len(resources))

    # ABB RW6 expects repeated form keys. The body is pre-encoded to preserve
    # those repeated keys while avoiding httpx.AsyncClient issues observed
    # when passing list-of-tuples form data through data=....
    response = await client.post("/subscription", content=payload)

    headers = dict(response.headers)
    ws_url_raw, group_id = _extract_ws_url_and_group_id(response.text, headers)
    ws_url = _normalize_ws_url(ws_url_raw, client)
    cookie_header = client.session_cookie_header()
    initial_values = _parse_events(response.text, lookup)

    logger.info("Subscription created: group_id=%s, ws_url=%s", group_id, ws_url)

    return SubscriptionHandle(
        group_id=group_id,
        ws_url=ws_url,
        cookie_header=cookie_header,
        resources=tuple(resources),
        initial_values=initial_values,
    )


async def delete_subscription(client: RWSClient, handle: SubscriptionHandle) -> None:
    """Delete an ABB RWS subscription group through HTTP fallback cleanup.

    Route: ``DELETE /subscription/{group-id}``

    ABB constraints: This explicit HTTP cleanup is intended for the case where
        the subscription group was created but the WebSocket stream was never
        opened. Once the WebSocket has been opened and then closed, ABB RW6
        cleans up the group server-side and may reject a later HTTP DELETE
        with ``Group <id> does not belong to Client <id>``.

    Args:
        client: Open RWSClient instance.
        handle: Handle returned by ``create_subscription``.

    Returns:
        None.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: If the group was already removed.
        RWSHTTPError: On any other HTTP status greater than or equal to 400.

    Example:
        ```python
        >>> await delete_subscription(client, handle)
        ```
    """
    logger.info("Deleting subscription group_id=%s", handle.group_id)

    await client.delete(f"/subscription/{handle.group_id}")

    logger.info("Subscription group_id=%s deleted", handle.group_id)


async def watch_resources(
    client: RWSClient,
    resources: Sequence[SubscribedResource],
    *,
    yield_initial_values: bool = True,
) -> AsyncGenerator[tuple[str, str], None]:
    """Subscribe to resources and yield ``(name, value)`` events as they occur.

    Route: ``POST /subscription`` then WebSocket ``ws://.../poll/{group-id}``.
        If the WebSocket was never opened, fallback cleanup uses
        ``DELETE /subscription/{group-id}``.

    ABB constraints:
        - WebSocket subprotocol must be ``robapi2_subscription``.
        - The WebSocket handshake must carry the same session cookies as the
          HTTP session.
        - ``compression=None`` disables permessage-deflate because some RW6
          controllers reject WebSocket extension negotiation.
        - ``ping_interval=None`` disables client-side WebSocket ping frames
          because ABB documents its own application-level ping/pong behavior.
        - When the WebSocket has been opened, ABB RW6 cleans up the
          subscription group when the WebSocket closes.
        - If the WebSocket was never opened, the subscription group is deleted
          explicitly with ``DELETE /subscription/{group-id}``.

    Args:
        client: Open RWSClient instance.
        resources: Resources to subscribe to.
        yield_initial_values: If ``True``, yield the initial values returned
            by ABB in the ``POST /subscription`` response before reading
            WebSocket events.

    Yields:
        ``(name, value)`` tuples, where ``name`` is the logical
        ``SubscribedResource.name`` and ``value`` is the raw ABB value string.

    Raises:
        ValueError: If the resource list is invalid or ABB's response cannot
            be parsed.
        RWSAuthenticationError: On HTTP 401 during subscription setup.
        RWSHTTPError: On HTTP errors during subscription setup.
        OSError: If the WebSocket connection cannot be established.

    Example:
        ```python
        >>> resources = [
        ...     SubscribedResource(
        ...         "a",
        ...         build_rapid_pers_resource_uri("T_ROB1", "M", "X"),
        ...         "1",
        ...     ),
        ...     SubscribedResource(
        ...         "b",
        ...         build_rapid_pers_resource_uri("T_ROB1", "M", "Y"),
        ...         "1",
        ...     ),
        ... ]
        >>> async for name, value in watch_resources(client, resources):
        ...     print(name, value)
        ```
    """
    lookup = _build_resource_lookup(resources)
    handle = await create_subscription(client, resources)
    websocket_opened = False

    try:
        if yield_initial_values:
            for name, value in handle.initial_values.items():
                yield name, value

        # ABB RW6 WebSocket notes confirmed on real hardware:
        # - subprotocol must be "robapi2_subscription";
        # - compression must be disabled to avoid rejected extension negotiation;
        # - ping_interval is disabled to avoid extra client-side ping frames.
        async with websockets.asyncio.client.connect(
            handle.ws_url,
            additional_headers={"Cookie": handle.cookie_header},
            subprotocols=_RWS_SUBPROTOCOLS,
            open_timeout=10.0,
            ping_interval=None,
            compression=None,
        ) as websocket:
            websocket_opened = True
            logger.info("WebSocket connected: %s", handle.ws_url)

            async for message in websocket:
                text = str(message)
                logger.debug("WebSocket message: %s", text)

                for name, value in _parse_events(text, lookup).items():
                    yield name, value

    finally:
        if websocket_opened:
            logger.info(
                "Subscription group_id=%s cleanup delegated to WebSocket close",
                handle.group_id,
            )
        else:
            try:
                await delete_subscription(client, handle)
            except Exception as exc:
                # Teardown must never raise: a failed cleanup must not hide
                # the original subscription or WebSocket setup error.
                logger.warning(
                    "Could not delete subscription group_id=%s: %s",
                    handle.group_id,
                    exc,
                )
