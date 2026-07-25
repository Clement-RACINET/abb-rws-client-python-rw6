# abb_rws_client/highlevel/variables.py
"""High-level RAPID variable read/write for ABB RWS RobotWare 6.

Author: Clement RACINET

Composed operations built exclusively from atomic ``rws/`` functions.
No HTTP calls are made directly in this module.

All functions are async and require an open ``RWSClient`` instance.
"""

from __future__ import annotations

import re

import httpx

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.rws.mastership import (
    post_mastership_domain_release,
    post_mastership_domain_request,
)
from abb_rws_client_python_rw6.rws.rapid.symbol import (
    get_rapid_symbol_data,
    update_rapid_variable_current_value,
)

logger = get_logger(__name__)


def _parse_symbol_value(response: httpx.Response) -> str:
    """Extract the ``value`` field from a RAPID symbol data response.

    Args:
        response: Raw HTTP response from ``get_rapid_symbol_data``.

    Returns:
        The symbol value as a string (as returned by the controller).

    Raises:
        ValueError: If the value cannot be extracted from the response body.

    Example:
        ```python
        resp = await get_rapid_symbol_data(client, symbolurl="RAPID/T_ROB1/M/x")
        val = _parse_symbol_value(resp)
        # val == "42"
        ```
    """
    # JSON path: {"state": [{"value": "...", ...}]}
    try:
        data = response.json()
        states = data.get("state", [])
        if states and "value" in states[0]:
            return str(states[0]["value"])
    except Exception:
        pass

    # XML / HTML path: <span class="value">...</span>
    match = re.search(
        r'class=["\']value["\'][^>]*>([^<]+)<',
        response.text,
    )
    if match:
        return match.group(1).strip()

    raise ValueError(f"Cannot parse symbol value from response: {response.text[:200]}")


# ---------------------------------------------------------------------------
# Mastership-guarded variable write
# ---------------------------------------------------------------------------


async def set_variable_with_mastership(
    client: RWSClient,
    *,
    symbolurl: str,
    value: str,
    domain: str = "rapid",
) -> None:
    """Write a RAPID variable value, acquiring and releasing mastership.

    Composes:

    1. ``post_mastership_domain_request(domain, action="request")``
    2. ``update_rapid_variable_current_value(action="set", value=value)``
    3. ``post_mastership_domain_release(domain, action="release")``

    Mastership is **always** released in a ``finally`` block, even if
    the write fails, to avoid leaving the controller locked.

    Route (delegated):
        - ``POST /rw/mastership/{domain}`` (action=request)
        - ``POST /rw/rapid/symbol/data/{symbolurl}`` (action=set)
        - ``POST /rw/mastership/{domain}`` (action=release)

    ABB constraints:
        - Requires AUTO mode for mastership.
        - ``symbolurl`` format: ``RAPID/T_ROB1/MainModule/my_var``
        - ``domain`` must be one of: ``"rapid"``, ``"cfg"``, ``"motion"``.

    Args:
        client: Open ``RWSClient`` instance.
        symbolurl: Full RAPID symbol path, e.g.
            ``"RAPID/T_ROB1/MainModule/counter"``.
        value: New value as a string. Numeric types must be
            pre-converted: ``str(42)``, ``str(3.14)``.
        domain: Mastership domain. Defaults to ``"rapid"``.

    Returns:
        None. Expects HTTP 204 on the write call.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/target_x",
                value="250.0",
            )
        ```
    """
    # Acquire mastership on the specified domain
    await post_mastership_domain_request(client, domain=domain, action="request")
    try:
        await update_rapid_variable_current_value(
            client,
            symbolurl=symbolurl,
            action="set",
            value=value,
        )
        logger.debug("Variable %s set to %r", symbolurl, value)
    finally:
        # Always release — even on exception — to avoid locking the controller
        await post_mastership_domain_release(client, domain=domain, action="release")


async def set_variables_with_mastership(
    client: RWSClient,
    *,
    values: dict[str, str],
    domain: str = "rapid",
) -> None:
    """Write multiple RAPID variables while holding mastership once.

    Requests mastership a single time, writes every ``symbolurl -> value``
    pair sequentially, then releases mastership in a ``finally`` block.
    More efficient than calling ``set_variable_with_mastership`` in a
    loop, which would request/release mastership once per variable.

    Route (delegated):
        - ``POST /rw/mastership/{domain}`` (action=request)
        - ``POST /rw/rapid/symbol/data/{symbolurl}`` (action=set), once per entry
        - ``POST /rw/mastership/{domain}`` (action=release)

    ABB constraints:
        - Requires AUTO mode for mastership.
        - ``domain`` must be one of: ``"rapid"``, ``"cfg"``, ``"motion"``.

    Args:
        client: Open ``RWSClient`` instance.
        values: Mapping of ``symbolurl -> value``. Values must already
            be pre-converted to strings.
        domain: Mastership domain. Defaults to ``"rapid"``.

    Returns:
        None. Expects HTTP 204 on each write call.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400 — mastership is still
            released before the exception propagates.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            await set_variables_with_mastership(
                client,
                values={
                    "RAPID/T_ROB1/M/x": "1",
                    "RAPID/T_ROB1/M/y": "2",
                },
            )
        ```
    """
    await post_mastership_domain_request(client, domain=domain, action="request")
    try:
        for symbolurl, value in values.items():
            await update_rapid_variable_current_value(
                client,
                symbolurl=symbolurl,
                action="set",
                value=value,
            )
            logger.debug("Variable %s set to %r", symbolurl, value)
    finally:
        await post_mastership_domain_release(client, domain=domain, action="release")


async def get_variable(
    client: RWSClient,
    *,
    symbolurl: str,
) -> str:
    """Read a RAPID variable value.

    Wraps ``get_rapid_symbol_data`` and extracts the ``value`` field
    from the response body.

    Route (delegated): ``GET /rw/rapid/symbol/data/{symbolurl}``

    ABB constraints:
        - No mastership required for reads.
        - ``symbolurl`` format: ``RAPID/T_ROB1/MainModule/my_var``

    Args:
        client: Open ``RWSClient`` instance.
        symbolurl: Full RAPID symbol path, e.g.
            ``"RAPID/T_ROB1/MainModule/counter"``.

    Returns:
        The variable value as a string, exactly as returned by the
        controller (e.g. ``"42"``, ``"TRUE"``,
        ``"[[250,0,300],[1,0,0,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]]"``).

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.
        ValueError: If the value cannot be parsed from the response.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            val = await get_variable(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/counter",
            )
            print("counter =", val)
        ```
    """
    response = await get_rapid_symbol_data(client, symbolurl=symbolurl)
    return _parse_symbol_value(response)
