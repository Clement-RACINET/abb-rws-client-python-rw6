# abb_rws_client/highlevel/panel.py
"""High-level controller motor state for ABB RWS RobotWare 6.

Author: Clement RACINET

Composed operations built exclusively from atomic ``rws/`` functions.
No HTTP calls are made directly in this module.

All functions are async and require an open ``RWSClient`` instance.
"""

from __future__ import annotations

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.rws.panel import set_controller_state

logger = get_logger(__name__)


async def set_motors_on(client: RWSClient) -> None:
    """Switch the controller to motors-on state.

    Wraps ``set_controller_state`` with ``ctrl_state="motoron"``.

    Route (delegated): ``POST /rw/panel/ctrlstate`` (action=setctrlstate)

    ABB constraints:
        - Controller must be in AUTO mode.
        - No mastership required.

    Args:
        client: Open ``RWSClient`` instance.

    Returns:
        None. Expects HTTP 204.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_motors_on(client)
        ```
    """
    await set_controller_state(
        client,
        action="setctrlstate",
        ctrl_state="motoron",
    )
    logger.debug("Motors ON")


async def set_motors_off(client: RWSClient) -> None:
    """Switch the controller to motors-off state.

    Wraps ``set_controller_state`` with ``ctrl_state="motoroff"``.

    Route (delegated): ``POST /rw/panel/ctrlstate`` (action=setctrlstate)

    ABB constraints:
        - No mastership required.

    Args:
        client: Open ``RWSClient`` instance.

    Returns:
        None. Expects HTTP 204.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_motors_off(client)
        ```
    """
    await set_controller_state(
        client,
        action="setctrlstate",
        ctrl_state="motoroff",
    )
    logger.debug("Motors OFF")
