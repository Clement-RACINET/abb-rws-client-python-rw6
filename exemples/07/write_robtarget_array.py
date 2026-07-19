#!/usr/bin/env python3
# exemples/07/write_robtarget_array.py
"""Example 07 — Write an array of robtargets to a RAPID PERS variable.

This example writes a RAPID PERS robtarget array element by element via RWS.

Important ABB/RWS details:
    - RAPID arrays use braces: TrajectoryPoints{1}, not TrajectoryPoints[1].
    - In the RWS URL, braces must be percent-encoded:
        TrajectoryPoints%7B1%7D
    - A robtarget is a RAPID complex value, not a string.
      Therefore the value is sent without outer double quotes:
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,...]]
    - Mastership is acquired once for the whole batch through the high-level
      wrapper set_variables_with_mastership(...).

Prerequisites:
    - Controller in AUTO mode.
    - RAPID stopped.
    - Module RobtargetArray loaded in T_ROB1.
    - Variable declared as:
        PERS robtarget TrajectoryPoints{10} := [...]
"""

from __future__ import annotations

import asyncio
import sys
from urllib.parse import quote

from abb_rws_client_python_rw6 import (
    RobTarget,
    RWSClient,
    configure_logging,
    get_logger,
    load_env,
    robtarget_to_rws,
)
from abb_rws_client_python_rw6.core.exceptions import RWSError
from abb_rws_client_python_rw6.highlevel.rapid import (
    get_variable,
    is_running,
    set_variables_with_mastership,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

load_env()
configure_logging("INFO")
logger = get_logger("examples.write_robtarget_array_highlevel_batch")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TASK = "T_ROB1"
MODULE = "RobtargetArray"
ARRAY_VAR = "TrajectoryPoints"

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
    # eax defaults to [9E+9] * 6
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def symbol_url_element(
    task: str,
    module: str,
    variable: str,
    index: int,
) -> str:
    """Build a RWS symbolurl for one RAPID array element.

    RAPID syntax:
        TrajectoryPoints{1}

    RWS URL-safe syntax:
        TrajectoryPoints%7B1%7D

    Example:
        RAPID/T_ROB1/RobtargetArray/TrajectoryPoints%7B1%7D
    """
    raw_symbolurl = f"RAPID/{task}/{module}/{variable}{{{index}}}"
    return quote(raw_symbolurl, safe="/")


def robtarget_rws_value(rt: RobTarget) -> str:
    """Serialize a RobTarget for RWS variable write.

    For a RAPID robtarget variable, send the RAPID literal directly.

    Correct:
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,...]]

    Not this:
        "[[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,...]]"
    """
    return robtarget_to_rws(rt)


def make_demo_trajectory(n: int, base: RobTarget) -> list[RobTarget]:
    """Generate n demo robtargets along X, spaced by 10 mm."""
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
# RWS operations
# ---------------------------------------------------------------------------


async def write_robtarget_array_batch(
    client: RWSClient,
    *,
    task: str,
    module: str,
    variable: str,
    points: list[RobTarget],
) -> None:
    """Write a list of RobTargets into a RAPID PERS robtarget array.

    Uses one mastership session for the whole batch.
    """
    values: dict[str, str] = {}

    for i, point in enumerate(points, start=1):
        symbolurl = symbol_url_element(
            task=task,
            module=module,
            variable=variable,
            index=i,
        )
        value = robtarget_rws_value(point)

        values[symbolurl] = value

        logger.info(
            "[%d/%d] Prepared %s = %s",
            i,
            len(points),
            symbolurl,
            value,
        )

    logger.info(
        "Writing %d robtargets with one mastership session.",
        len(values),
    )

    await set_variables_with_mastership(
        client,
        values=values,
        domain="rapid",
    )

    logger.info("Write complete — %d points written.", len(points))


async def read_robtarget_element(
    client: RWSClient,
    *,
    task: str,
    module: str,
    variable: str,
    index: int,
) -> str:
    """Read one robtarget element from the RAPID array."""
    symbolurl = symbol_url_element(
        task=task,
        module=module,
        variable=variable,
        index=index,
    )

    return await get_variable(
        client,
        symbolurl=symbolurl,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the robtarget array write example."""
    n_points = 5
    points = make_demo_trajectory(n_points, DEFAULT_ROBTARGET)

    logger.info(
        "Demo trajectory: %d points, base x=%.0f y=%.0f z=%.0f",
        n_points,
        DEFAULT_ROBTARGET.x,
        DEFAULT_ROBTARGET.y,
        DEFAULT_ROBTARGET.z,
    )

    for i, pt in enumerate(points, start=1):
        logger.info(
            "  [%d] x=%.1f y=%.1f z=%.1f → %s",
            i,
            pt.x,
            pt.y,
            pt.z,
            robtarget_rws_value(pt),
        )

    try:
        async with RWSClient() as client:
            logger.info("Connected → %s", client.base_url)

            if await is_running(client):
                logger.error("RAPID is running. Stop RAPID before writing PERS variables.")
                sys.exit(1)

            await write_robtarget_array_batch(
                client,
                task=TASK,
                module=MODULE,
                variable=ARRAY_VAR,
                points=points,
            )

            logger.info("Verifying first and last elements…")

            val_1 = await read_robtarget_element(
                client,
                task=TASK,
                module=MODULE,
                variable=ARRAY_VAR,
                index=1,
            )

            val_n = await read_robtarget_element(
                client,
                task=TASK,
                module=MODULE,
                variable=ARRAY_VAR,
                index=n_points,
            )

            logger.info("  [1] = %s", val_1)
            logger.info("  [%d] = %s", n_points, val_n)

            logger.info("Done.")

    except RWSError as exc:
        logger.error("RWS error: %s", exc)
        sys.exit(1)

    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
