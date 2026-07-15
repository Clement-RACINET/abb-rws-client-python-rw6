# abb_rws_client/_core/logging.py
"""Centralised logging configuration for abb-rws-client-python-rw6.

The entire library uses the standard :mod:`logging` module with loggers
named after their module (``logging.getLogger(__name__)``).  All of them
are children of the root logger ``"abb_rws_client"``, so a single call to
:func:`configure_logging` is enough to control verbosity for the whole
library without touching the application's own loggers.

Default behaviour (no call to :func:`configure_logging`):
    The ``"abb_rws_client"`` logger has **no handler and no level set**,
    which means it inherits from the root Python logger.  In practice the
    library is silent unless the caller configures logging themselves.

Typical usage — application code::

    from abb_rws_client import configure_logging
    configure_logging(level="DEBUG")

Typical usage — examples / scripts::

    import os
    from abb_rws_client import configure_logging
    configure_logging(level=os.getenv("RWS_LOG_LEVEL", "INFO"))

Typical usage — tests (silence the library)::

    from abb_rws_client import configure_logging
    configure_logging(level="WARNING")
"""

from __future__ import annotations

import logging
import sys
from typing import TextIO

#: Name of the library root logger.  Every sub-logger (``_core.client``,
#: ``highlevel.rapid``, ``rws.rapid.execution``, …) is a child of this one.
_ROOT_LOGGER_NAME: str = "abb_rws_client"

#: Default format string used when no *fmt* argument is provided.
_DEFAULT_FMT: str = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DEFAULT_DATE_FMT: str = "%H:%M:%S"


def configure_logging(
    level: int | str = logging.WARNING,
    fmt: str = _DEFAULT_FMT,
    date_fmt: str = _DEFAULT_DATE_FMT,
    handler: logging.Handler | None = None,
    stream: TextIO = sys.stderr,
) -> logging.Logger:
    """Configure the ``abb_rws_client`` root logger.

    Installs a :class:`logging.StreamHandler` (or a custom *handler*) on
    the ``"abb_rws_client"`` logger and sets its level.  Calling this
    function more than once replaces the existing handlers.

    All child loggers (``abb_rws_client._core.client``,
    ``abb_rws_client.highlevel.rapid``, ``abb_rws_client.rws.*``, …)
    inherit this configuration automatically — no per-module setup needed.

    Args:
        level: Logging level for the library.  Accepts an integer
            (e.g. ``logging.DEBUG``) or a string (e.g. ``"DEBUG"``,
            ``"INFO"``, ``"WARNING"``).  Defaults to ``logging.WARNING``
            (silent in production).
        fmt: Log record format string (``logging`` style).
            Defaults to ``"%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"``.
        date_fmt: Date/time format string passed to the formatter.
            Defaults to ``"%H:%M:%S"``.
        handler: Custom :class:`logging.Handler` to attach.  When
            ``None`` a :class:`logging.StreamHandler` writing to *stream*
            is created automatically.
        stream: Output stream used when *handler* is ``None``.
            Defaults to :data:`sys.stderr`.

    Returns:
        The configured ``"abb_rws_client"`` :class:`logging.Logger`
        instance (useful for immediate use or further customisation).

    Raises:
        ValueError: If *level* is a string that is not a recognised
            logging level name.

    Example:
        Basic setup for a script::

            from abb_rws_client import configure_logging
            configure_logging(level="DEBUG")

        Custom handler (e.g. file)::

            import logging
            from abb_rws_client import configure_logging

            fh = logging.FileHandler("rws.log")
            configure_logging(level="INFO", handler=fh)

        Read level from environment::

            import os
            from abb_rws_client import configure_logging
            configure_logging(level=os.getenv("RWS_LOG_LEVEL", "WARNING"))
    """
    # Resolve string level → int (raises ValueError on unknown name)
    if isinstance(level, str):
        numeric = logging.getLevelName(level.upper())
        if not isinstance(numeric, int):
            raise ValueError(
                f"Unknown logging level: {level!r}. "
                f"Expected one of DEBUG, INFO, WARNING, ERROR, CRITICAL."
            )
        level = numeric

    lib_logger = logging.getLogger(_ROOT_LOGGER_NAME)

    # Replace existing handlers to avoid duplicate output on repeated calls.
    lib_logger.handlers.clear()

    if handler is None:
        handler = logging.StreamHandler(stream)

    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=date_fmt))
    lib_logger.addHandler(handler)
    lib_logger.setLevel(level)

    # Do not propagate to the root Python logger — the library manages its
    # own output and should not interfere with the application's log config.
    lib_logger.propagate = False

    return lib_logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of ``"abb_rws_client"``.

    Convenience wrapper so that any module — including user code and
    example scripts — can obtain a properly namespaced logger without
    hard-coding the root name.

    Args:
        name: Sub-name appended to ``"abb_rws_client."``.
            Typically ``__name__`` of the calling module, or a short
            descriptive label (e.g. ``"examples.ping"``).

    Returns:
        A :class:`logging.Logger` named
        ``"abb_rws_client.<name>"``.

    Example:
        Inside a library module::

            from abb_rws_client._core.logging import get_logger
            logger = get_logger(__name__)

        Inside an example script::

            from abb_rws_client import get_logger
            logger = get_logger("examples.ping")
    """
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
