#!/usr/bin/env python3
# exemples/07/write_robtarget_array.py
"""Example 07 — Write an array of robtargets to a RAPID PERS variable.

Author: Clement RACINET

Demonstrates the non-trivial aspects of writing a robtarget array via RWS:

1. RWS does NOT support writing an entire array in one POST.
   Each element must be written individually via its 1-based index:
   ``POST /rw/rapid/symbol/data/RAPID/T_ROB1/M/MyArray[1]``
   ``POST /rw/rapid/symbol/data/RAPID/T_ROB1/M/MyArray[2]``
   ...

2. The robtarget value string MUST be wrapped in double-quotes in the
   body, exactly like a RAPID string type. The controller rejects the
   request with HTTP 400 if the quotes are missing.
   Correct body: ``value="[[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,...]]"``

3. Mastership must be acquired ONCE before the loop and released
   in a ``try/finally`` block — acquiring/releasing per element
   would be extremely slow and risks deadlock.

4. Array indexing in RAPID is 1-based.

5. The robtarget string length can exceed RWS single-request limits
   if the full array is sent at once — writing element by element
   avoids this constraint entirely.

Prerequisites:
    - Controller in AUTO mode, RAPID stopped (PP at main, STOP executed).
    - Module ``RobtargetArray`` loaded in T_ROB1
      (see ``exemples/07/RobtargetArray.mod``).
    - ``.env`` at the repository root with ``RWS_HOST``.

Run:
    pixi run -e examples example-07
"""
from __future__ import annotations

import asyncio
import sys

from abb_rws_client_python_rw6 import (
    RobTarget,
    RWSClient,
    configure_logging,
    get_logger,
    load_env,
    robtarget_to_rws,
)
from abb_rws_client_python_rw6.core.exceptions import RWSError
from abb_rws_client_python_rw6.rws.mastership import (
    post_mastership_domain_release,
    post_mastership_domain_request,
)
from abb_rws_client_python_rw6.rws.rapid.symbol import (
    get_rapid_symbol_data,
    update_rapid_variable_current_value,
)

load_env()
configure_logging("INFO")
logger = get_logger("examples.write_robtarget_array")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TASK: str = "T_ROB1"
MODULE: str = "RobtargetArray"
ARRAY_VAR: str = "TrajectoryPoints"

#: Default reference position for this cell.
#: trans=[1500, 0, 1789], rot=[0,0,1,0] (180° around Z), no ext axes.
DEFAULT_ROBTARGET = RobTarget(
    x=1500.0,
    y=0.0,
    z=1789.0,
    qw=0.0,
    qx=0.0,
    qy=1.0,
    qz=0.0,
    cf1=0.0,
    cf4=0.0,
    cf6=0.0,
    cfx=0.0,
    # eax defaults to [9E+9]*6
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _symbol_url_element(task: str, module: str, variable: str, index: int) -> str:
    """Build a RWS symbolurl for a single RAPID array element.

    RAPID arrays are 1-based. Index 0 in Python → index 1 in RAPID.

    Args:
        task: RAPID task name (e.g. ``"T_ROB1"``).
        module: RAPID module name.
        variable: RAPID array variable name.
        index: 1-based RAPID index.

    Returns:
        symbolurl string, e.g.
        ``"RAPID/T_ROB1/RobtargetArray/TrajectoryPoints[3]"``.

    Example:
        ::

            _symbol_url_element("T_ROB1", "M", "pts", 2)
            # → "RAPID/T_ROB1/M/pts[2]"
    """
    return f"RAPID/{task}/{module}/{variable}[{index}]"


def _robtarget_rws_value(rt: RobTarget) -> str:
    """Serialize a RobTarget into the RWS body value string.

    A robtarget sent via RWS POST body must be wrapped in double-quotes,
    exactly like a RAPID string. Without quotes, the controller returns
    HTTP 400.

    Reference (ABB doc):
        ``value="[[x,y,z],[qw,qx,qy,qz],[cf1,cf4,cf6,cfx],[eax...]]"``

    Args:
        rt: RobTarget instance to serialize.

    Returns:
        Quoted RWS value string ready for the ``value=`` body parameter.

    Example:
        ::

            _robtarget_rws_value(RobTarget(x=1500, y=0, z=1789))
            # → '"[[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,...]]"'
    """
    return f'"{robtarget_to_rws(rt)}"'


def _make_demo_trajectory(n: int, base: RobTarget) -> list[RobTarget]:
    """Generate demo robtargets as a straight line along X from the base position.

    Args:
        n: Number of points to generate.
        base: Reference RobTarget. Each point offsets X by ``i * 10`` mm.

    Returns:
        List of ``n`` RobTarget instances spaced 10 mm apart along X,
        all other fields copied from ``base``.

    Example:
        ::

            pts = _make_demo_trajectory(3, DEFAULT_ROBTARGET)
            # pts[0].x == 1500.0
            # pts[1].x == 1510.0
            # pts[2].x == 1520.0
    """
    return [
        RobTarget(
            x=base.x + float(i * 10),
            y=base.y,
            z=base.z,
            qw=base.qw,
            qx=base.qx,
            qy=base.qy,
            qz=base.qz,
            cf1=base.cf1,
            cf4=base.cf4,
            cf6=base.cf6,
            cfx=base.cfx,
            eax=list(base.eax),
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Core write function
# ---------------------------------------------------------------------------


async def write_robtarget_array(
    client: RWSClient,
    task: str,
    module: str,
    variable: str,
    points: list[RobTarget],
) -> None:
    """Write a list of RobTargets into a RAPID PERS array, element by element.

    Acquires RAPID mastership once, writes all elements in a loop
    using 1-based RAPID indexing, then releases mastership in a
    ``finally`` block.

    The value string sent in the POST body is wrapped in double-quotes
    as required by ABB RWS for non-num types.

    Route:
        ``POST /rw/rapid/symbol/data/RAPID/{task}/{module}/{var}[{i}]``
        ``?action=set``
        Body: ``value="[[x,y,z],[qw,qx,qy,qz],[cf1,cf4,cf6,cfx],[eax...]]"``

    ABB constraints:
        - RAPID mastership required in AUTO mode.
        - Array must be declared ``PERS robtarget`` in the RAPID module.
        - Array size in RAPID must be >= ``len(points)``.
        - RWS does NOT support writing the full array in one request
          (character limit exceeded for large arrays).
        - Index is 1-based (RAPID convention).
        - Value must be quoted (double-quotes) in the body.

    Args:
        client: Open :class:`~abb_rws_client_python_rw6.RWSClient` instance.
        task: RAPID task name (e.g. ``"T_ROB1"``).
        module: RAPID module name containing the array.
        variable: RAPID array variable name (must be ``PERS robtarget{N}``).
        points: List of RobTarget instances to write.
            ``points[0]`` → RAPID index ``[1]``.

    Raises:
        RWSHTTPError: On any HTTP error during mastership or write.
        RWSValueError: If a RobTarget cannot be serialized.

    Example:
        ::

            pts = [RobTarget(x=1500.0 + i*10, y=0, z=1789) for i in range(5)]
            async with RWSClient() as client:
                await write_robtarget_array(
                    client, "T_ROB1", "RobtargetArray", "TrajectoryPoints", pts
                )
    """
    logger.info(
        "Writing %d robtargets → RAPID/%s/%s/%s",
        len(points),
        task,
        module,
        variable,
    )

    # ── Acquire mastership once for the entire batch ───────────────────────
    await post_mastership_domain_request(client, domain="rapid")
    logger.debug("Mastership acquired")

    try:
        for i, point in enumerate(points):
            rapid_index = i + 1  # RAPID arrays are 1-based
            symbol = _symbol_url_element(task, module, variable, rapid_index)

            # Value MUST be quoted for non-num RAPID types
            rws_value = _robtarget_rws_value(point)

            logger.debug(
                "  [%d/%d] %s = %s",
                rapid_index,
                len(points),
                symbol,
                rws_value,
            )

            await update_rapid_variable_current_value(
                client,
                symbolurl=symbol,
                action="set",
                value=rws_value,
            )

    finally:
        # ── Always release mastership, even on error ───────────────────────
        await post_mastership_domain_release(client, domain="rapid")
        logger.debug("Mastership released")

    logger.info("Write complete — %d points written.", len(points))


# ---------------------------------------------------------------------------
# Verify: read back one element
# ---------------------------------------------------------------------------


async def read_robtarget_element(
    client: RWSClient,
    task: str,
    module: str,
    variable: str,
    index: int,
) -> str:
    """Read a single robtarget element from a RAPID PERS array.

    Route:
        ``GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{variable}[{index}]``

    ABB constraints:
        - Index is 1-based (RAPID convention).
        - No mastership required for read.

    Args:
        client: Open RWSClient instance.
        task: RAPID task name.
        module: RAPID module name.
        variable: RAPID array variable name.
        index: 1-based element index.

    Returns:
        Raw RWS value string as returned by the controller.

    Raises:
        RWSHTTPError: On HTTP error.
        ValueError: If the value cannot be parsed from the response.

    Example:
        ::

            val = await read_robtarget_element(
                client, "T_ROB1", "RobtargetArray", "TrajectoryPoints", 1
            )
            # → '[[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,...]]'
    """
    import re  # noqa: PLC0415

    symbol = _symbol_url_element(task, module, variable, index)
    response = await get_rapid_symbol_data(client, symbolurl=symbol)

    match = re.search(r'class=["\']value["\'][^>]*>([^<]+)<', response.text)
    if match:
        return match.group(1).strip()
    try:
        data = response.json()
        states = data.get("state", [])
        if states and "value" in states[0]:
            return str(states[0]["value"])
    except Exception:  # noqa: BLE001
        pass
    raise ValueError(f"Cannot parse value from response: {response.text[:200]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the robtarget array write example."""
    n_points = 5
    points = _make_demo_trajectory(n_points, DEFAULT_ROBTARGET)

    logger.info("Demo trajectory: %d points (base: x=%.0f y=%.0f z=%.0f)",
                n_points, DEFAULT_ROBTARGET.x, DEFAULT_ROBTARGET.y, DEFAULT_ROBTARGET.z)
    for i, pt in enumerate(points):
        logger.info("  [%d] x=%.1f y=%.1f z=%.1f → %s",
                    i + 1, pt.x, pt.y, pt.z, _robtarget_rws_value(pt))

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            # ── Write ──────────────────────────────────────────────────────
            await write_robtarget_array(
                client, TASK, MODULE, ARRAY_VAR, points
            )

            # ── Read back first and last to verify ────────────────────────
            logger.info("Verifying…")
            val_1 = await read_robtarget_element(
                client, TASK, MODULE, ARRAY_VAR, 1
            )
            val_n = await read_robtarget_element(
                client, TASK, MODULE, ARRAY_VAR, n_points
            )
            logger.info("  [1] = %s", val_1)
            logger.info("  [%d] = %s", n_points, val_n)
            logger.info("Done.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
