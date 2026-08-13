# tests/highlevel/test_subscription.py
"""Unit tests for abb_rws_client_python_rw6.highlevel.subscription.

Author: Clement RACINET

Covers: payload/limit validation, resource lookup construction, XML event
parsing (both ABB-documented shapes), WebSocket URL / group id extraction,
loopback normalization, and the full create/delete/watch lifecycle with
httpx and websockets mocked (no real controller involved).
"""

from __future__ import annotations

from collections.abc import Sequence
import contextlib

import httpx
import pytest

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.highlevel import subscription as sub
from abb_rws_client_python_rw6.highlevel.subscription import (
    SubscribedResource,
    SubscriptionHandle,
)

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _build_fake_response(
    headers: dict[str, str],
    text: str,
    status_code: int = 201,
) -> httpx.Response:
    """Build a real httpx.Response for tests, avoiding a hand-rolled fake type.

    Using the real httpx.Response class (instead of a custom dataclass)
    guarantees exact type compatibility with what create_subscription
    actually receives from RWSClient.post at runtime.

    Args:
        headers: Response headers to simulate (e.g. "Location").
        text: Response body text.
        status_code: HTTP status code (default: 201, matching ABB's
            documented success code for POST /subscription).

    Returns:
        A real httpx.Response instance.
    """
    return httpx.Response(status_code=status_code, headers=headers, text=text)


class _FakeRWSClient(RWSClient):
    """Test double for RWSClient, overriding only the network-touching methods.

    Subclasses RWSClient (rather than duck-typing an unrelated class) so
    that static type checkers accept it wherever a RWSClient is expected,
    without resorting to cast() or type: ignore comments. super().__init__
    only sets plain attributes (host, username, password, port, timeout,
    base_url) and leaves self._http as None; no real HTTP session is opened.
    """

    def __init__(self, host: str = "192.168.125.1") -> None:
        super().__init__(host=host)
        self.post_calls: list[tuple[str, dict[str, object]]] = []
        self._post_response: httpx.Response | None = None
        self._fake_cookie_header = "-http-session-=abc123; ABBCX=xyz789"

    def set_post_response(self, response: httpx.Response) -> None:
        """Configure the response returned by the next post() call."""
        self._post_response = response

    async def post(self, path: str, **kwargs: object) -> httpx.Response:
        """Record the call and return the pre-configured fake response."""
        self.post_calls.append((path, kwargs))
        assert self._post_response is not None, "post() called without a configured response"
        return self._post_response

    def session_cookie_header(self) -> str:
        """Return a fixed fake cookie header, mirroring RWSClient's sync method."""
        return self._fake_cookie_header


class _FakeWebSocketConnection:
    """Async context manager + async iterator standing in for a websockets connection."""

    def __init__(self, messages: list[str]) -> None:
        self._messages = list(messages)

    async def __aenter__(self) -> _FakeWebSocketConnection:
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False

    def __aiter__(self) -> _FakeWebSocketConnection:
        return self

    async def __anext__(self) -> str:
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)


def _fake_connect(url: str, **kwargs: object) -> _FakeWebSocketConnection:
    """Default no-message WebSocket connect stub, overridden per-test as needed."""
    return _FakeWebSocketConnection([])


# ---------------------------------------------------------------------------
# build_rapid_pers_resource_uri
# ---------------------------------------------------------------------------


def test_build_rapid_pers_resource_uri_nominal() -> None:
    """Nominal case: builds the exact ABB symbol-data URI for a PERS variable."""
    uri = sub.build_rapid_pers_resource_uri("T_ROB1", "Subscription", "WatchedValue")
    assert uri == "/rw/rapid/symbol/data/RAPID/T_ROB1/Subscription/WatchedValue;value"


# ---------------------------------------------------------------------------
# _validate_resources
# ---------------------------------------------------------------------------


def test_validate_resources_empty_raises() -> None:
    """Error case: an empty resource list is rejected before any HTTP call."""
    with pytest.raises(ValueError, match="at least one"):
        sub._validate_resources([])


def test_validate_resources_too_many_total_raises() -> None:
    """Error case: exceeding ABB's 1000-resource hard limit is rejected."""
    resources = [
        SubscribedResource(f"r{i}", f"/rw/iosystem/signals/S{i};state", "0")
        for i in range(sub._MAX_RESOURCES_TOTAL + 1)
    ]
    with pytest.raises(ValueError, match="1000"):
        sub._validate_resources(resources)


def test_validate_resources_too_many_high_priority_raises() -> None:
    """Error case: exceeding ABB's 64-resource High-priority limit is rejected."""
    resources = [
        SubscribedResource(f"r{i}", f"/rw/iosystem/signals/S{i};state", "2")
        for i in range(sub._MAX_HIGH_PRIORITY_RESOURCES + 1)
    ]
    with pytest.raises(ValueError, match="64"):
        sub._validate_resources(resources)


def test_validate_resources_valid_passes() -> None:
    """Nominal case: a valid resource list raises nothing."""
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]
    sub._validate_resources(resources)  # Must not raise.


# ---------------------------------------------------------------------------
# _build_subscription_payload
# ---------------------------------------------------------------------------


def test_build_subscription_payload_single_resource() -> None:
    """Nominal case: single resource → resources=1, 1=<uri>, 1-p=<priority>."""
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "2")]
    payload = sub._build_subscription_payload(resources)
    assert payload == {"resources": "1", "1": "/rw/iosystem/signals/A;state", "1-p": "2"}


def test_build_subscription_payload_multiple_resources() -> None:
    """Edge case: multiple resources → indices are 1-based and ordered."""
    resources = [
        SubscribedResource("a", "/rw/iosystem/signals/A;state", "1"),
        SubscribedResource("b", "/rw/iosystem/signals/B;state", "0"),
    ]
    payload = sub._build_subscription_payload(resources)
    assert payload == {
        "resources": "2",
        "1": "/rw/iosystem/signals/A;state",
        "1-p": "1",
        "2": "/rw/iosystem/signals/B;state",
        "2-p": "0",
    }


# ---------------------------------------------------------------------------
# _build_resource_lookup
# ---------------------------------------------------------------------------


def test_build_resource_lookup_rapid_symbol_registers_both_forms() -> None:
    """Nominal case: a RAPID PERS resource is looked up by full URI AND bare symbolurl."""
    resource = SubscribedResource(
        "watched",
        sub.build_rapid_pers_resource_uri("T_ROB1", "M", "X"),
        "1",
    )
    lookup = sub._build_resource_lookup([resource])
    assert lookup["/rw/rapid/symbol/data/RAPID/T_ROB1/M/X;value"] == "watched"
    assert lookup["RAPID/T_ROB1/M/X"] == "watched"


def test_build_resource_lookup_io_signal_registers_only_full_uri() -> None:
    """Edge case: a non-RAPID resource (IO signal) has no bare-symbolurl alias."""
    resource = SubscribedResource("do1", "/rw/iosystem/signals/Virtual1/Board1/do1;state", "0")
    lookup = sub._build_resource_lookup([resource])
    assert lookup == {"/rw/iosystem/signals/Virtual1/Board1/do1;state": "do1"}


# ---------------------------------------------------------------------------
# _extract_li_blocks
# ---------------------------------------------------------------------------


def test_extract_li_blocks_splits_multiple_blocks() -> None:
    """Nominal case: two sibling <li> blocks are returned as two separate strings."""
    text = '<li class="a">1</li><li class="b">2</li>'
    blocks = sub._extract_li_blocks(text)
    assert len(blocks) == 2
    assert '"a"' in blocks[0]
    assert '"b"' in blocks[1]


def test_extract_li_blocks_no_match_returns_empty_list() -> None:
    """Edge case: text with no <li> block returns an empty list."""
    assert sub._extract_li_blocks("<div>no list here</div>") == []


# ---------------------------------------------------------------------------
# _extract_resource_identity
# ---------------------------------------------------------------------------


def test_extract_resource_identity_from_href() -> None:
    """Nominal case: <a href="..."> carries the full resource URI."""
    block = (
        '<li class="ios-signalstate-ev"><a href="/rw/iosystem/signals/A;state" rel="self"/></li>'
    )
    assert sub._extract_resource_identity(block) == "/rw/iosystem/signals/A;state"


def test_extract_resource_identity_from_title_with_slash() -> None:
    """Nominal case: title containing '/' (bare symbolurl) is treated as identity."""
    block = '<li class="rap-data" title="RAPID/T_ROB1/M/X"><span class="value">1</span></li>'
    assert sub._extract_resource_identity(block) == "RAPID/T_ROB1/M/X"


def test_extract_resource_identity_from_generic_title_returns_none() -> None:
    """Edge case: a generic title with no '/' carries no resolvable identity."""
    block = '<li class="rap-value-ev" title="value"><span class="value">1</span></li>'
    assert sub._extract_resource_identity(block) is None


def test_extract_resource_identity_no_match_returns_none() -> None:
    """Error case: a block with neither href nor title returns None."""
    assert sub._extract_resource_identity("<li>plain</li>") is None


# ---------------------------------------------------------------------------
# _extract_value
# ---------------------------------------------------------------------------


def test_extract_value_from_value_class() -> None:
    """Nominal case: <span class="value"> is matched (RAPID events)."""
    block = '<li><span class="value">42</span></li>'
    assert sub._extract_value(block) == "42"


def test_extract_value_from_lvalue_class() -> None:
    """Nominal case: <span class="lvalue"> is matched (IO signal events)."""
    block = '<li><span class="lvalue">1</span></li>'
    assert sub._extract_value(block) == "1"


def test_extract_value_no_span_returns_none() -> None:
    """Edge case: a block with no value span returns None."""
    assert sub._extract_value("<li>no value here</li>") is None


# ---------------------------------------------------------------------------
# _parse_events
# ---------------------------------------------------------------------------


def test_parse_events_single_block_io_signal() -> None:
    """Nominal case: ABB doc's generic IO signal event (identity+value in one <li>)."""
    text = (
        '<li class="ios-signalstate-ev">'
        '<a href="/rw/iosystem/signals/Virtual1/Board1/do1;state" rel="self"/>'
        '<span class="lvalue">1</span>'
        "</li>"
    )
    lookup = {"/rw/iosystem/signals/Virtual1/Board1/do1;state": "do1"}
    assert sub._parse_events(text, lookup) == {"do1": "1"}


def test_parse_events_split_block_rapid_pers_variable() -> None:
    """Nominal case: RAPID PERS event split across an '-ev' <li> and a 'rap-data' <li>.

    Fixture built from the ABB-documented sample discussed earlier in this
    conversation; not independently re-verified against a live capture — see
    the TODO in create_subscription for the multi-resource caveat this shares.
    """
    text = (
        '<li class="rap-value-ev" title="value">'
        '<a href="/rw/rapid/symbol/data/RAPID/T_ROB1/M/X;value" rel="self"/>'
        "</li>"
        '<li class="rap-data" title="RAPID/T_ROB1/M/X">'
        '<span class="value">99</span>'
        "</li>"
    )
    lookup = sub._build_resource_lookup(
        [SubscribedResource("watched", "/rw/rapid/symbol/data/RAPID/T_ROB1/M/X;value", "1")]
    )
    assert sub._parse_events(text, lookup) == {"watched": "99"}


def test_parse_events_unsubscribed_resource_ignored() -> None:
    """Edge case: an event for a resource outside the lookup is silently dropped."""
    text = (
        '<li class="ios-signalstate-ev">'
        '<a href="/rw/iosystem/signals/Other;state" rel="self"/>'
        '<span class="lvalue">1</span>'
        "</li>"
    )
    assert sub._parse_events(text, lookup={}) == {}


def test_parse_events_value_with_no_pending_identity_ignored() -> None:
    """Edge case: a value span with no prior identity block yields no event."""
    text = '<li class="rap-data" title="value"><span class="value">1</span></li>'
    assert sub._parse_events(text, lookup={"x": "name"}) == {}


# ---------------------------------------------------------------------------
# _extract_ws_url_and_group_id
# ---------------------------------------------------------------------------


def test_extract_ws_url_and_group_id_from_location_header() -> None:
    """Nominal case: WebSocket URL taken from the Location header."""
    ws_url, group_id = sub._extract_ws_url_and_group_id(
        response_text="",
        headers={"Location": "ws://192.168.125.1:80/poll/9"},
    )
    assert ws_url == "ws://192.168.125.1:80/poll/9"
    assert group_id == "9"


def test_extract_ws_url_and_group_id_fallback_to_body_href() -> None:
    """Edge case: no Location header, WebSocket URL recovered from body <a href>."""
    ws_url, group_id = sub._extract_ws_url_and_group_id(
        response_text='<a href="ws://192.168.125.1:80/poll/3" rel="self"/>',
        headers={"Content-Type": "text/xml"},
    )
    assert ws_url == "ws://192.168.125.1:80/poll/3"
    assert group_id == "3"


def test_extract_ws_url_and_group_id_missing_url_raises() -> None:
    """Error case: neither Location header nor body href present."""
    with pytest.raises(ValueError, match="Could not extract WebSocket URL"):
        sub._extract_ws_url_and_group_id(response_text="<li>no ws url</li>", headers={})


def test_extract_ws_url_and_group_id_missing_group_id_raises() -> None:
    """Error case: WebSocket URL found but with no '/poll/<id>' pattern."""
    with pytest.raises(ValueError, match="group id"):
        sub._extract_ws_url_and_group_id(
            response_text="",
            headers={"Location": "ws://192.168.125.1:80/other/path"},
        )


# ---------------------------------------------------------------------------
# _normalize_ws_url
# ---------------------------------------------------------------------------


def test_normalize_ws_url_replaces_loopback_ip() -> None:
    """Nominal case: 127.0.0.1 in the ABB WebSocket URL is replaced by the real host."""
    client = _FakeRWSClient(host="192.168.125.1")
    result = sub._normalize_ws_url("ws://127.0.0.1:80/poll/9", client)
    assert result == "ws://192.168.125.1:80/poll/9"


def test_normalize_ws_url_replaces_localhost() -> None:
    """Edge case: 'localhost' is replaced the same way as 127.0.0.1."""
    client = _FakeRWSClient(host="192.168.125.1")
    result = sub._normalize_ws_url("ws://localhost:80/poll/9", client)
    assert result == "ws://192.168.125.1:80/poll/9"


def test_normalize_ws_url_leaves_real_host_unchanged() -> None:
    """Nominal case: a non-loopback host is left untouched."""
    client = _FakeRWSClient(host="192.168.125.1")
    result = sub._normalize_ws_url("ws://10.0.0.5:80/poll/9", client)
    assert result == "ws://10.0.0.5:80/poll/9"


# ---------------------------------------------------------------------------
# create_subscription
# ---------------------------------------------------------------------------


async def test_create_subscription_nominal() -> None:
    """Nominal case: single resource, full round trip against the fake client."""
    client = _FakeRWSClient()
    client.set_post_response(
        _build_fake_response(
            headers={"Location": "ws://127.0.0.1:80/poll/7"},
            text=(
                '<li class="ios-signalstate-ev">'
                '<a href="/rw/iosystem/signals/A;state" rel="self"/>'
                '<span class="lvalue">1</span>'
                "</li>"
            ),
        )
    )
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]

    handle = await sub.create_subscription(client, resources)

    assert handle.group_id == "7"
    assert handle.ws_url == "ws://192.168.125.1:80/poll/7"  # loopback normalized
    assert handle.cookie_header == "-http-session-=abc123; ABBCX=xyz789"
    assert handle.initial_values == {"a": "1"}
    # Payload actually sent to ABB, format-checked.
    path, kwargs = client.post_calls[0]
    assert path == "/subscription"
    assert kwargs["data"] == {"resources": "1", "1": "/rw/iosystem/signals/A;state", "1-p": "1"}


async def test_create_subscription_invalid_resources_raises_before_http_call() -> None:
    """Error case: validation failure happens before any HTTP request is sent."""
    client = _FakeRWSClient()
    with pytest.raises(ValueError, match="at least one"):
        await sub.create_subscription(client, [])
    assert client.post_calls == []


async def test_create_subscription_unparsable_response_raises() -> None:
    """Error case: ABB response missing both Location header and body href."""
    client = _FakeRWSClient()
    client.set_post_response(_build_fake_response(headers={}, text="<li>nothing usable</li>"))
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]

    with pytest.raises(ValueError, match="Could not extract WebSocket URL"):
        await sub.create_subscription(client, resources)


# ---------------------------------------------------------------------------
# delete_subscription
# ---------------------------------------------------------------------------


async def test_delete_subscription_calls_rws_delete_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nominal case: delete_subscription forwards to the generated RWS DELETE call."""
    calls: list[tuple[RWSClient, str]] = []

    async def fake_unsubscribe(client: RWSClient, group_id: str) -> httpx.Response:
        calls.append((client, group_id))
        return httpx.Response(status_code=200)

    monkeypatch.setattr(
        sub, "unsubscribe_or_remove_the_subscription_group_resources", fake_unsubscribe
    )

    client = _FakeRWSClient()
    handle = SubscriptionHandle(
        group_id="7",
        ws_url="ws://192.168.125.1:80/poll/7",
        cookie_header="cookie",
        resources=(),
        initial_values={},
    )
    await sub.delete_subscription(client, handle)

    assert calls == [(client, "7")]


# ---------------------------------------------------------------------------
# watch_resources
# ---------------------------------------------------------------------------


async def test_watch_resources_yields_initial_then_ws_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nominal case: initial values, then parsed WebSocket events, then teardown."""
    handle = SubscriptionHandle(
        group_id="7",
        ws_url="ws://192.168.125.1:80/poll/7",
        cookie_header="-http-session-=abc; ABBCX=xyz",
        resources=(SubscribedResource("a", "/rw/iosystem/signals/A;state", "1"),),
        initial_values={"a": "0"},
    )

    async def fake_create_subscription(
        client: RWSClient, resources: Sequence[SubscribedResource]
    ) -> SubscriptionHandle:
        return handle

    delete_calls: list[SubscriptionHandle] = []

    async def fake_delete_subscription(client: RWSClient, h: SubscriptionHandle) -> None:
        delete_calls.append(h)

    ws_message = (
        '<li class="ios-signalstate-ev">'
        '<a href="/rw/iosystem/signals/A;state" rel="self"/>'
        '<span class="lvalue">1</span>'
        "</li>"
    )
    connect_calls: list[dict[str, object]] = []

    def fake_connect(url: str, **kwargs: object) -> _FakeWebSocketConnection:
        connect_calls.append({"url": url, **kwargs})
        return _FakeWebSocketConnection([ws_message])

    monkeypatch.setattr(sub, "create_subscription", fake_create_subscription)
    monkeypatch.setattr(sub, "delete_subscription", fake_delete_subscription)
    monkeypatch.setattr(sub.websockets.asyncio.client, "connect", fake_connect)

    client = _FakeRWSClient()
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]

    events = [event async for event in sub.watch_resources(client, resources)]

    assert events == [("a", "0"), ("a", "1")]
    assert delete_calls == [handle]
    assert connect_calls[0]["url"] == "ws://192.168.125.1:80/poll/7"
    assert connect_calls[0]["additional_headers"] == {"Cookie": "-http-session-=abc; ABBCX=xyz"}
    assert connect_calls[0]["subprotocols"] == sub._RWS_SUBPROTOCOLS
    assert connect_calls[0]["compression"] is None


async def test_watch_resources_skips_initial_values_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Edge case: yield_initial_values=False skips the initial-values step entirely."""
    handle = SubscriptionHandle(
        group_id="7",
        ws_url="ws://192.168.125.1:80/poll/7",
        cookie_header="cookie",
        resources=(SubscribedResource("a", "/rw/iosystem/signals/A;state", "1"),),
        initial_values={"a": "0"},
    )

    async def fake_create_subscription(
        client: RWSClient, resources: Sequence[SubscribedResource]
    ) -> SubscriptionHandle:
        return handle

    async def fake_delete_subscription(client: RWSClient, h: SubscriptionHandle) -> None:
        return None

    monkeypatch.setattr(sub, "create_subscription", fake_create_subscription)
    monkeypatch.setattr(sub, "delete_subscription", fake_delete_subscription)
    monkeypatch.setattr(sub.websockets.asyncio.client, "connect", _fake_connect)

    client = _FakeRWSClient()
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]

    events = [
        event async for event in sub.watch_resources(client, resources, yield_initial_values=False)
    ]

    assert events == []


async def test_watch_resources_deletes_subscription_on_consumer_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error case: an exception while consuming the generator still tears down the group.

    Uses contextlib.aclosing: raising inside a bare `async for` loop does NOT
    call aclose() on the generator (same Python semantics as a plain `for`
    loop) — the generator's own `finally` would only run non-deterministically
    on garbage collection. aclosing() forces a deterministic aclose().
    """
    handle = SubscriptionHandle(
        group_id="7",
        ws_url="ws://192.168.125.1:80/poll/7",
        cookie_header="cookie",
        resources=(SubscribedResource("a", "/rw/iosystem/signals/A;state", "1"),),
        initial_values={"a": "0"},
    )

    async def fake_create_subscription(
        client: RWSClient, resources: Sequence[SubscribedResource]
    ) -> SubscriptionHandle:
        return handle

    delete_calls: list[SubscriptionHandle] = []

    async def fake_delete_subscription(client: RWSClient, h: SubscriptionHandle) -> None:
        delete_calls.append(h)

    monkeypatch.setattr(sub, "create_subscription", fake_create_subscription)
    monkeypatch.setattr(sub, "delete_subscription", fake_delete_subscription)
    monkeypatch.setattr(sub.websockets.asyncio.client, "connect", _fake_connect)

    client = _FakeRWSClient()
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]

    with pytest.raises(RuntimeError, match="boom"):
        async with contextlib.aclosing(sub.watch_resources(client, resources)) as events:
            async for _name, _value in events:
                raise RuntimeError("boom")

    assert delete_calls == [handle]


async def test_watch_resources_teardown_failure_does_not_mask_original_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error case: DELETE failing during teardown must not mask the original error."""
    handle = SubscriptionHandle(
        group_id="7",
        ws_url="ws://192.168.125.1:80/poll/7",
        cookie_header="cookie",
        resources=(SubscribedResource("a", "/rw/iosystem/signals/A;state", "1"),),
        initial_values={"a": "0"},  # Non-empty: the loop must run at least once
        # to actually reach the `raise` in the test body below.
    )

    async def fake_create_subscription(
        client: RWSClient, resources: Sequence[SubscribedResource]
    ) -> SubscriptionHandle:
        return handle

    async def failing_delete_subscription(client: RWSClient, h: SubscriptionHandle) -> None:
        raise RuntimeError("controller unreachable during teardown")

    monkeypatch.setattr(sub, "create_subscription", fake_create_subscription)
    monkeypatch.setattr(sub, "delete_subscription", failing_delete_subscription)
    monkeypatch.setattr(sub.websockets.asyncio.client, "connect", _fake_connect)

    client = _FakeRWSClient()
    resources = [SubscribedResource("a", "/rw/iosystem/signals/A;state", "1")]

    with pytest.raises(RuntimeError, match="original consumer error"):
        async with contextlib.aclosing(sub.watch_resources(client, resources)) as events:
            async for _name, _value in events:
                raise RuntimeError("original consumer error")
