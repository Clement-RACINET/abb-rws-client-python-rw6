# abb_rws_client/core/env.py
"""Environment configuration loader for abb_rws_client_python_rw6.

Author: Clement RACINET

Resolves and loads a ``.env`` file into :data:`os.environ` using
:mod:`python-dotenv` (already a runtime dependency).  The lookup walks
up the directory tree from a given starting point, so it works correctly
regardless of the current working directory or script nesting depth.

This module is part of the library's public API. Any application or script can
call :func:`load_env` to bootstrap the environment before instantiating
:class:`~abb_rws_client_python_rw6.RWSClient`.

Environment variables recognised by :class:`~abb_rws_client_python_rw6.RWSClient`:
    - ``RWS_HOST``     : Controller IP or hostname (required if not passed explicitly).
    - ``RWS_USER``     : RWS username (default: ``"Default User"``).
    - ``RWS_PASSWORD`` : RWS password (default: ``"robotics"``).
    - ``RWS_PORT``     : HTTP port as integer string (default: ``"80"``).
    - ``RWS_TIMEOUT``  : HTTP timeout in seconds as float string (default: no timeout).
                         Set to a number (e.g. ``"30"``) to limit request duration.
    - ``RWS_LOG_LEVEL``: Logging level for :func:`~abb_rws_client_python_rw6.configure_logging`
                         (default: ``"WARNING"``).
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env(
    env_path: Path | str | None = None,
    *,
    override: bool = False,
) -> Path | None:
    """Locate and load a ``.env`` file into :data:`os.environ`.

    Uses :func:`dotenv.load_dotenv` under the hood (``python-dotenv``).
    When *env_path* is ``None``, the function walks up the directory tree
    starting from the **caller's file location** (via :data:`Path.cwd`)
    until it finds a ``.env`` file or reaches the filesystem root.

    Already-set variables are **never overwritten** unless *override* is
    ``True`` — safe to call multiple times.

    Args:
        env_path: Explicit path to a ``.env`` file or directory
            containing one.  When ``None``, the function searches
            upward from :func:`Path.cwd`.
        override: When ``True``, existing environment variables are
            overwritten by values from the ``.env`` file.  Defaults to
            ``False`` (``os.environ.setdefault`` semantics).

    Returns:
        The resolved :class:`Path` of the loaded ``.env`` file, or
        ``None`` if no file was found (no error is raised).

    Raises:
        FileNotFoundError: If *env_path* is given explicitly but does
            not exist.

    Example:
        Automatic discovery from current working directory::

            from abb_rws_client_python_rw6import load_env
            load_env()

        Explicit path::

            from abb_rws_client_python_rw6import load_env
            from pathlib import Path
            load_env(Path("/etc/myrobot/.env"))

        Override existing variables::

            from abb_rws_client_python_rw6import load_env
            load_env(override=True)
    """
    try:
        from dotenv import load_dotenv  # python-dotenv
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "python-dotenv is required for load_env(). Install it with: pip install python-dotenv"
        ) from exc

    resolved: Path | None

    if env_path is not None:
        resolved = Path(env_path).resolve()
        if resolved.is_dir():
            resolved = resolved / ".env"
        if not resolved.is_file():
            raise FileNotFoundError(f".env file not found: {resolved}")
    else:
        resolved = _find_env(Path.cwd())
        if resolved is None:
            return None

    load_dotenv(dotenv_path=resolved, override=override)
    return resolved


def _find_env(start: Path) -> Path | None:
    """Walk up the directory tree looking for a ``.env`` file.

    Args:
        start: Directory from which to begin the upward search.

    Returns:
        The first ``.env`` :class:`Path` found, or ``None`` if the
        filesystem root is reached without finding one.

    Example:
        >>> from pathlib import Path
        >>> from abb_rws_client_python_rw6.core.env import _find_env
        >>> _find_env(Path("/home/user/projects/robot/examples/02"))
        PosixPath('/home/user/projects/robot/.env')  # if it exists there
    """
    current = start
    while True:
        candidate = current / ".env"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def get_env_str(key: str, default: str) -> str:
    """Read a string environment variable with a fallback default.

    Args:
        key: Environment variable name.
        default: Value returned when the variable is absent or empty.

    Returns:
        The environment variable value, or *default*.

    Example:
        >>> host = get_env_str("RWS_HOST", "192.168.125.1")
    """
    return os.environ.get(key, default) or default


def get_env_int(key: str, default: int) -> int:
    """Read an integer environment variable with a fallback default.

    Args:
        key: Environment variable name.
        default: Value returned when the variable is absent, empty,
            or not a valid integer.

    Returns:
        The parsed integer value, or *default*.

    Example:
        >>> port = get_env_int("RWS_PORT", 80)
    """
    raw = os.environ.get(key, "")
    try:
        return int(raw)
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """Read a float environment variable with a fallback default.

    Args:
        key: Environment variable name.
        default: Value returned when the variable is absent, empty,
            or not a valid float.

    Returns:
        The parsed float value, or *default*.

    Example:
        >>> timeout = get_env_float("RWS_TIMEOUT", 10.0)
    """
    raw = os.environ.get(key, "")
    try:
        return float(raw)
    except ValueError:
        return default


def get_env_float_or_none(key: str, default: float | None) -> float | None:
    """Read a float-or-None environment variable with a fallback default.

    Accepts ``"none"``, ``"inf"``, ``"infinite"``, ``"infinity"``
    (case-insensitive) as special string values mapping to ``None``
    (no timeout). When the variable is absent or empty, *default* is
    returned as-is.

    Args:
        key: Environment variable name.
        default: Value returned when the variable is absent, empty, or invalid.

    Returns:
        The parsed float, ``None`` (no timeout), or *default*.

    Example:
        >>> timeout = get_env_float_or_none("RWS_TIMEOUT", None)
        >>> timeout is None  # → no timeout
        True
    """
    raw = os.environ.get(key, "").strip().lower()
    if not raw:
        return default
    if raw in {"none", "inf", "infinite", "infinity"}:
        return None
    try:
        return float(raw)
    except ValueError:
        return default
