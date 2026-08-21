# Subscription Priority

Source file: `subscription_priority.py`

```python
from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import mean
from time import perf_counter

from abb_rws_client_python_rw6 import load_env
from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import configure_logging
from abb_rws_client_python_rw6.highlevel.subscription import (
    SubscribedResource,
    SubscriptionPriority,
    build_rapid_pers_resource_uri,
    watch_resources,
)


@dataclass
class EventStats:
    """Runtime statistics for one subscribed ABB RWS resource.

    Route: N/A — local statistics container.

    ABB constraints: None. The measured values are client-side inter-arrival
        intervals, not controller-side source latency.

    Args:
        count: Number of events received for the resource.
        last_value: Last value received from ABB.
        last_timestamp: Local monotonic timestamp of the last event.
        intervals_ms: Client-side intervals between consecutive events.

    Returns:
        EventStats instance.

    Raises:
        No exception is raised by this data container.

    Example:
        ```python
        >>> stats = EventStats()
        >>> stats.count
        0
        ```
    """

    count: int = 0
    last_value: str | None = None
    last_timestamp: float | None = None
    intervals_ms: list[float] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable interval storage.

        Route: N/A — local dataclass initializer.

        ABB constraints: None.

        Args:
            None.

        Returns:
            None.

        Raises:
            No exception is raised by this initializer.

        Example:
            ```python
            >>> stats = EventStats()
            >>> stats.intervals_ms
            []
            ```
        """
        if self.intervals_ms is None:
            self.intervals_ms = []


def _parse_priority(value: str) -> SubscriptionPriority:
    """Convert a CLI priority string to a strict ABB subscription priority.

    Route: N/A — local CLI validation helper.

    ABB constraints: ABB RWS subscription priorities are ``"0"``, ``"1"``
        and ``"2"``.

    Args:
        value: Raw CLI priority value.

    Returns:
        Valid ABB subscription priority.

    Raises:
        argparse.ArgumentTypeError: If the priority is not valid.

    Example:
        ```python
        >>> _parse_priority("2")
        '2'
        ```
    """
    if value == "0":
        return "0"
    if value == "1":
        return "1"
    if value == "2":
        return "2"

    raise argparse.ArgumentTypeError('priority must be "0", "1", or "2"')


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the priority example.

    Route: N/A — local CLI helper.

    ABB constraints: High priority ``"2"`` is applicable only to PERS RAPID
        variables and IO signals. This example uses PERS RAPID variables.

    Args:
        None.

    Returns:
        Parsed command-line arguments.

    Raises:
        SystemExit: If argparse detects invalid command-line arguments.

    Example:
        ```powershell
        pixi run -e examples python examples/08/subscription_priority.py --priority 2
        ```
    """
    parser = argparse.ArgumentParser(
        description="Compare ABB RWS subscription event delivery priorities.",
    )
    parser.add_argument(
        "--priority",
        type=_parse_priority,
        default="1",
        help='ABB priority: "0"=Low, "1"=Medium, "2"=High.',
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=20.0,
        help="Measurement duration in seconds.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level.",
    )
    parser.add_argument(
        "--print-events",
        action="store_true",
        help="Print every received event.",
    )
    return parser.parse_args()


def _build_resources(priority: SubscriptionPriority) -> list[SubscribedResource]:
    """Build the RAPID PERS resources used by the priority test.

    Route: N/A — local resource builder.

    ABB constraints: The RAPID module ``SubscriptionPriority`` must be loaded,
        and ``FastValue1`` / ``FastValue2`` must be declared as ``PERS num``.

    Args:
        priority: ABB subscription priority applied to all watched resources.

    Returns:
        List of resources to subscribe to.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> resources = _build_resources("1")
        >>> resources[0].name
        'fast_value_1'
        ```
    """
    return [
        SubscribedResource(
            name="fast_value_1",
            resource_uri=build_rapid_pers_resource_uri(
                "T_ROB1",
                "SubscriptionPriority",
                "FastValue1",
            ),
            priority=priority,
        ),
        SubscribedResource(
            name="fast_value_2",
            resource_uri=build_rapid_pers_resource_uri(
                "T_ROB1",
                "SubscriptionPriority",
                "FastValue2",
            ),
            priority=priority,
        ),
    ]


def _format_resources(resources: Sequence[SubscribedResource]) -> str:
    """Format subscribed resources for console output.

    Route: N/A — local display helper.

    ABB constraints: None.

    Args:
        resources: Resources to format.

    Returns:
        Human-readable resource summary.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> _format_resources([SubscribedResource("x", "/rw/test;value", "1")])
        'x(priority=1)'
        ```
    """
    return ", ".join(f"{resource.name}(priority={resource.priority})" for resource in resources)


def _record_event(stats: EventStats, value: str, timestamp: float) -> None:
    """Record one received ABB subscription event.

    Route: N/A — local statistics helper.

    ABB constraints: The timestamp is measured locally in Python and is not a
        controller-side event timestamp.

    Args:
        stats: Statistics object to update.
        value: Raw value received from ABB RWS.
        timestamp: Current monotonic timestamp.

    Returns:
        None.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> stats = EventStats()
        >>> _record_event(stats, "1", 10.0)
        >>> stats.count
        1
        ```
    """
    if stats.last_timestamp is not None and stats.intervals_ms is not None:
        stats.intervals_ms.append((timestamp - stats.last_timestamp) * 1000.0)

    stats.count += 1
    stats.last_value = value
    stats.last_timestamp = timestamp


def _print_summary(
    priority: SubscriptionPriority,
    duration_s: float,
    stats_by_name: dict[str, EventStats],
) -> None:
    """Print a summary of received ABB RWS subscription events.

    Route: N/A — local reporting helper.

    ABB constraints: The summary reports client-side received event frequency.
        It does not prove exact controller-side latency.

    Args:
        priority: ABB priority used during the subscription.
        duration_s: Measurement duration in seconds.
        stats_by_name: Statistics keyed by resource logical name.

    Returns:
        None.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> _print_summary("1", 10.0, {"x": EventStats(count=3)})
        ```
    """
    print()
    print("[summary]")
    print(f"  priority : {priority}")
    print(f"  duration : {duration_s:.1f} s")

    for name, stats in stats_by_name.items():
        intervals = stats.intervals_ms or []
        rate_hz = stats.count / duration_s if duration_s > 0.0 else 0.0

        print(f"  {name}:")
        print(f"    events     : {stats.count}")
        print(f"    rate       : {rate_hz:.2f} Hz")
        print(f"    last value : {stats.last_value}")

        if intervals:
            print(f"    dt mean    : {mean(intervals):.1f} ms")
            print(f"    dt min     : {min(intervals):.1f} ms")
            print(f"    dt max     : {max(intervals):.1f} ms")
        else:
            print("    dt mean    : n/a")
            print("    dt min     : n/a")
            print("    dt max     : n/a")


async def _run_measurement(
    client: RWSClient,
    resources: Sequence[SubscribedResource],
    duration_s: float,
    print_events: bool,
) -> dict[str, EventStats]:
    """Run the RWS subscription priority measurement.

    Route: ``POST /subscription`` then WebSocket ``ws://.../poll/{group-id}``.

    ABB constraints:
        - Priority ``"2"`` is valid for PERS RAPID variables and IO signals.
        - Priority ``"1"`` has a documented maximum event delay of 200 ms.
        - Priority ``"0"`` has a documented maximum event delay of 5 seconds.

    Args:
        client: Open ABB RWS client.
        resources: Resources to subscribe to.
        duration_s: Measurement duration in seconds.
        print_events: If ``True``, print every event received.

    Returns:
        Statistics keyed by resource logical name.

    Raises:
        RWSAuthenticationError: If authentication fails.
        RWSHTTPError: If ABB rejects the subscription.
        OSError: If the WebSocket cannot be opened.

    Example:
        ```python
        >>> stats = await _run_measurement(client, resources, 10.0, False)
        ```
    """
    deadline = perf_counter() + duration_s
    stats_by_name = {resource.name: EventStats() for resource in resources}

    async for name, value in watch_resources(client, resources):
        now = perf_counter()
        stats = stats_by_name[name]
        _record_event(stats, value, now)

        if print_events:
            print(f"[event] {name} = {value}")

        if now >= deadline:
            break

    return stats_by_name


async def main() -> None:
    """Run the ABB RWS subscription priority example.

    Route: ``POST /subscription`` then WebSocket ``ws://.../poll/{group-id}``.

    ABB constraints:
        - The RAPID module ``SubscriptionPriority`` must be loaded.
        - The RAPID task must be running.
        - Watched variables must be ``PERS``.
        - High priority is valid for PERS RAPID variables and IO signals.

    Args:
        None.

    Returns:
        None.

    Raises:
        RWSAuthenticationError: If authentication fails.
        RWSHTTPError: If ABB rejects the subscription request.
        OSError: If the WebSocket connection cannot be established.

    Example:
        ```powershell
        pixi run -e examples python examples/08/subscription_priority.py --priority 2
        ```
    """
    args = _parse_args()
    priority: SubscriptionPriority = args.priority
    duration_s = float(args.duration)

    configure_logging(str(args.log_level).upper())
    load_env()

    resources = _build_resources(priority)

    print(f"[main] Watching {_format_resources(resources)}")
    print(f"[main] Measurement duration: {duration_s:.1f} s")
    print("[main] Load examples/08/SubscriptionPriority.mod on the controller.")
    print("[main] Start RAPID execution if not already running.")
    print("[main] Press Ctrl+C to stop.")
    print()

    async with RWSClient() as client:
        print(f"[main] Connected to {client.host}:{client.port}")

        stats_by_name = await _run_measurement(
            client=client,
            resources=resources,
            duration_s=duration_s,
            print_events=bool(args.print_events),
        )

    _print_summary(priority, duration_s, stats_by_name)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("[main] Ctrl+C — stopping…")
        print("[main] Done.")
```
