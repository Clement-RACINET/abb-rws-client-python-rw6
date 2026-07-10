# abb_rws_client/_core/__init__.py
"""Internal core — session, exceptions, serializers.

Not part of the public API. Import from ``abb_rws_client`` directly.
"""

from __future__ import annotations

from .client import RWSClient, RWSClientSync
from .exceptions import RWSError, RWSConnectionError, RWSTimeoutError, RWSAuthenticationError, RWSHTTPError, RWSNotFoundError, MastershipError, MastershipDenied, MastershipNotHeld, RWSValueError, CTRL_CODES
from .serializers import RobTarget, RapidValue, robtarget_to_rws, rws_to_robtarget

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
    "robtarget_to_rws",
    "rws_to_robtarget",
]
