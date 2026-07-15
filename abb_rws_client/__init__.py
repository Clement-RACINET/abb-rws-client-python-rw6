# abb_rws_client/__init__.py
"""abb_rws_client_python_rw6 — Async Python client for ABB RWS (RobotWare 6).

Public API surface:
    - RWSClient / RWSClientSync  : HTTP session management
    - RWSError hierarchy         : typed exceptions
    - RobTarget / RapidValue     : RAPID type helpers
    - robtarget_to_rws / rws_to_robtarget : serializers
    - load_env                   : .env file loader
    - configure_logging          : library log level
    - get_logger                 : namespaced child logger

Example:
    >>> from abb_rws_client import RWSClient
    >>> async with RWSClient(host="192.168.125.1") as client:
    ...     resp = await client.get("/rw/rapid/execution")
"""

from __future__ import annotations

from abb_rws_client.core.client import RWSClient, RWSClientSync
from abb_rws_client.core.env import load_env
from abb_rws_client.core.exceptions import (
    CTRL_CODES,
    MastershipDenied,
    MastershipError,
    MastershipNotHeld,
    RWSAuthenticationError,
    RWSConnectionError,
    RWSError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
    RWSValueError,
)
from abb_rws_client.core.logging import configure_logging, get_logger
from abb_rws_client.core.serializers import (
    RapidValue,
    RobTarget,
    robtarget_to_rws,
    rws_to_robtarget,
)

__all__ = [
    "CTRL_CODES",
    "MastershipDenied",
    "MastershipError",
    "MastershipNotHeld",
    "RWSAuthenticationError",
    "RWSClient",
    "RWSClientSync",
    "RWSConnectionError",
    "RWSError",
    "RWSHTTPError",
    "RWSNotFoundError",
    "RWSTimeoutError",
    "RWSValueError",
    "RapidValue",
    "RobTarget",
    "configure_logging",
    "get_logger",
    "load_env",
    "robtarget_to_rws",
    "rws_to_robtarget",
]

__version__ = "0.8.0"
