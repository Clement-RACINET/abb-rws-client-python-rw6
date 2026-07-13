# exemples/_env.py
"""Minimal .env loader for the examples directory.

Reads the ``.env`` file at the repository root and injects missing
variables into ``os.environ``.  Already-set variables are never
overwritten (``os.environ.setdefault`` semantics).

This module is intentionally **not** part of the ``abb_rws_client``
package.  It is a development-only helper for running the example
scripts locally.

Usage::

    from _env import load_env
    load_env()
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env(env_path: Path | None = None) -> None:
    """Load a ``.env`` file into ``os.environ``.

    Args:
        env_path: Explicit path to the ``.env`` file.  When ``None``
            the function walks up from this file's directory until it
            finds a ``.env`` or reaches the filesystem root.

    Returns:
        None.

    Example:
        >>> from _env import load_env
        >>> load_env()
    """
    if env_path is None:
        env_path = _find_env(Path(__file__).resolve().parent)
    if env_path is None or not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _find_env(start: Path) -> Path | None:
    """Walk up the directory tree looking for a ``.env`` file.

    Args:
        start: Directory from which to begin the search.

    Returns:
        The first ``.env`` ``Path`` found, or ``None``.
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
