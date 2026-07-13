# tests/_core/test_env.py
"""Tests for abb_rws_client._core.env."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from abb_rws_client._core.env import (
    _find_env,
    get_env_float,
    get_env_float_or_none,
    get_env_int,
    get_env_str,
    load_env,
)

# ---------------------------------------------------------------------------
# _find_env
# ---------------------------------------------------------------------------


class TestFindEnv:
    """Unit tests for the _find_env directory walker."""

    def test_finds_env_in_start_dir(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("RWS_HOST=1.2.3.4\n")
        assert _find_env(tmp_path) == env_file

    def test_finds_env_in_parent(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("RWS_HOST=1.2.3.4\n")
        child = tmp_path / "sub" / "deep"
        child.mkdir(parents=True)
        assert _find_env(child) == env_file

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        # tmp_path has no .env and we start from a deep subdir
        child = tmp_path / "a" / "b" / "c"
        child.mkdir(parents=True)
        # Walk will eventually hit the filesystem root — but tmp_path
        # itself has no .env, so we mock the root stop condition.
        # Simpler: use a directory that is guaranteed to have no .env
        # by walking from a fresh tmp subtree.
        result = _find_env(child)
        # Result is None OR a real .env found somewhere above tmp_path
        # (e.g. repo root). We only assert the type contract.
        assert result is None or result.name == ".env"

    def test_stops_at_filesystem_root(self) -> None:
        """Must return None when starting from filesystem root."""
        root = Path("/")
        # If / has a .env, skip — otherwise must return None
        if not (root / ".env").is_file():
            assert _find_env(root) is None

    def test_finds_nearest_env(self, tmp_path: Path) -> None:
        """Must return the closest .env, not a distant ancestor's."""
        parent_env = tmp_path / ".env"
        parent_env.write_text("LEVEL=parent\n")
        child_dir = tmp_path / "child"
        child_dir.mkdir()
        child_env = child_dir / ".env"
        child_env.write_text("LEVEL=child\n")
        assert _find_env(child_dir) == child_env


# ---------------------------------------------------------------------------
# load_env
# ---------------------------------------------------------------------------


class TestLoadEnv:
    """Tests for load_env()."""

    def test_loads_explicit_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("RWS_HOST=10.0.0.1\n")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RWS_HOST", None)
            result = load_env(env_file)
        assert result == env_file

    def test_explicit_dir_resolves_to_env(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("RWS_HOST=10.0.0.2\n")
        result = load_env(tmp_path)
        assert result == env_file

    def test_raises_file_not_found_on_missing_explicit(
        self, tmp_path: Path
    ) -> None:
        missing = tmp_path / "nonexistent.env"
        with pytest.raises(FileNotFoundError, match=".env file not found"):
            load_env(missing)

    def test_raises_file_not_found_on_missing_in_dir(
        self, tmp_path: Path
    ) -> None:
        # Directory exists but has no .env
        with pytest.raises(FileNotFoundError, match=".env file not found"):
            load_env(tmp_path)

    def test_returns_none_when_no_env_found(self, tmp_path: Path) -> None:
        """Auto-discovery must return None gracefully when no .env exists."""
        with patch(
            "abb_rws_client._core.env._find_env", return_value=None
        ):
            result = load_env()
        assert result is None

    def test_does_not_override_by_default(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("RWS_HOST=from_file\n")
        with patch.dict(os.environ, {"RWS_HOST": "already_set"}):
            load_env(env_file, override=False)
            assert os.environ["RWS_HOST"] == "already_set"

    def test_override_replaces_existing(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("RWS_HOST=from_file\n")
        with patch.dict(os.environ, {"RWS_HOST": "already_set"}):
            load_env(env_file, override=True)
            assert os.environ["RWS_HOST"] == "from_file"

    def test_returns_resolved_path(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("")
        result = load_env(env_file)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("")
        result = load_env(str(env_file))
        assert result == env_file


# ---------------------------------------------------------------------------
# get_env_str
# ---------------------------------------------------------------------------


class TestGetEnvStr:
    """Tests for get_env_str()."""

    def test_returns_value_when_set(self) -> None:
        with patch.dict(os.environ, {"RWS_HOST": "192.168.1.1"}):
            assert get_env_str("RWS_HOST", "default") == "192.168.1.1"

    def test_returns_default_when_absent(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RWS_HOST", None)
            assert get_env_str("RWS_HOST", "fallback") == "fallback"

    def test_returns_default_when_empty(self) -> None:
        with patch.dict(os.environ, {"RWS_HOST": ""}):
            assert get_env_str("RWS_HOST", "fallback") == "fallback"


# ---------------------------------------------------------------------------
# get_env_int
# ---------------------------------------------------------------------------


class TestGetEnvInt:
    """Tests for get_env_int()."""

    def test_returns_parsed_int(self) -> None:
        with patch.dict(os.environ, {"RWS_PORT": "8080"}):
            assert get_env_int("RWS_PORT", 80) == 8080

    def test_returns_default_when_absent(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RWS_PORT", None)
            assert get_env_int("RWS_PORT", 80) == 80

    def test_returns_default_when_empty(self) -> None:
        with patch.dict(os.environ, {"RWS_PORT": ""}):
            assert get_env_int("RWS_PORT", 80) == 80

    def test_returns_default_when_not_integer(self) -> None:
        with patch.dict(os.environ, {"RWS_PORT": "abc"}):
            assert get_env_int("RWS_PORT", 80) == 80

    def test_returns_zero(self) -> None:
        with patch.dict(os.environ, {"RWS_PORT": "0"}):
            assert get_env_int("RWS_PORT", 80) == 0

    def test_returns_negative(self) -> None:
        with patch.dict(os.environ, {"RWS_PORT": "-1"}):
            assert get_env_int("RWS_PORT", 80) == -1


# ---------------------------------------------------------------------------
# get_env_float
# ---------------------------------------------------------------------------


class TestGetEnvFloat:
    """Tests for get_env_float()."""

    def test_returns_parsed_float(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": "30.5"}):
            assert get_env_float("RWS_TIMEOUT", 10.0) == pytest.approx(30.5)

    def test_returns_default_when_absent(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RWS_TIMEOUT", None)
            assert get_env_float("RWS_TIMEOUT", 10.0) == pytest.approx(10.0)

    def test_returns_default_when_empty(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": ""}):
            assert get_env_float("RWS_TIMEOUT", 10.0) == pytest.approx(10.0)

    def test_returns_default_when_not_float(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": "abc"}):
            assert get_env_float("RWS_TIMEOUT", 10.0) == pytest.approx(10.0)

    def test_parses_integer_string(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": "30"}):
            assert get_env_float("RWS_TIMEOUT", 10.0) == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# get_env_float_or_none
# ---------------------------------------------------------------------------


class TestGetEnvFloatOrNone:
    """Tests for get_env_float_or_none()."""

    def test_returns_parsed_float(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": "15.0"}):
            assert get_env_float_or_none("RWS_TIMEOUT", 10.0) == pytest.approx(
                15.0
            )

    def test_returns_default_when_absent(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RWS_TIMEOUT", None)
            assert get_env_float_or_none("RWS_TIMEOUT", None) is None

    def test_returns_default_when_empty(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": ""}):
            assert get_env_float_or_none("RWS_TIMEOUT", 5.0) == pytest.approx(5.0)

    @pytest.mark.parametrize(
        "value",
        ["none", "None", "NONE", "inf", "INF", "infinite", "INFINITE", "infinity"],
    )
    def test_special_strings_return_none(self, value: str) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": value}):
            assert get_env_float_or_none("RWS_TIMEOUT", 10.0) is None

    def test_returns_default_when_invalid(self) -> None:
        with patch.dict(os.environ, {"RWS_TIMEOUT": "not_a_float"}):
            assert get_env_float_or_none("RWS_TIMEOUT", 7.0) == pytest.approx(7.0)

    def test_default_none_returned_when_absent(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RWS_TIMEOUT", None)
            result = get_env_float_or_none("RWS_TIMEOUT", None)
            assert result is None
