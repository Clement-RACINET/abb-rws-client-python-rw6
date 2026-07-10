# tests/conftest.py
"""
Global pytest configuration for abb-rws6-python-client test suite.

Declares the asyncio loop scope for pytest-asyncio >= 0.24 compatibility.
All async tests use a fresh event loop per function (default).
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# pytest-asyncio >= 0.24 : explicit loop scope declaration
# Required when asyncio_mode = "auto" is set in pyproject.toml.
# Without this, async test methods inside classes are not collected.
# ---------------------------------------------------------------------------

# This marker ensures all async test classes inherit the asyncio scope.
# Individual test functions decorated with @pytest.mark.asyncio are unaffected.
pytestmark = pytest.mark.asyncio(loop_scope="function")
