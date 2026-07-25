# tests/highlevel/test_variables.py
"""Tests for abb_rws_client_python_rw6.highlevel.variables.

All rws/ dependencies are mocked via unittest.mock.AsyncMock — no HTTP
calls are made.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from abb_rws_client_python_rw6.core.exceptions import RWSHTTPError
from abb_rws_client_python_rw6.highlevel.variables import (
    _parse_symbol_value,
    get_variable,
    set_variable_with_mastership,
    set_variables_with_mastership,
)

_MODULE = "abb_rws_client_python_rw6.highlevel.variables"


def _resp(body: str = "", status: int = 200) -> httpx.Response:
    """Build a minimal httpx.Response with a text body."""
    return httpx.Response(status_code=status, text=body)


def _json_resp(data: dict, status: int = 200) -> httpx.Response:  # type: ignore[type-arg]
    """Build a minimal httpx.Response with a JSON body."""
    return httpx.Response(
        status_code=status,
        content=json.dumps(data).encode(),
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def client() -> MagicMock:
    """Return a bare MagicMock acting as RWSClient."""
    return MagicMock()


# ---------------------------------------------------------------------------
# _parse_symbol_value
# ---------------------------------------------------------------------------


class TestParseSymbolValue:
    """Unit tests for the _parse_symbol_value helper."""

    def test_json_value(self) -> None:
        assert _parse_symbol_value(_json_resp({"state": [{"value": "42"}]})) == "42"

    def test_xml_value(self) -> None:
        assert _parse_symbol_value(_resp('<span class="value">TRUE</span>')) == "TRUE"

    def test_raises_on_unparseable(self) -> None:
        with pytest.raises(ValueError, match="symbol value"):
            _parse_symbol_value(_resp("<html></html>"))

    def test_json_value_numeric_cast(self) -> None:
        """Numeric values stored as int in JSON must be cast to str."""
        assert _parse_symbol_value(_json_resp({"state": [{"value": 99}]})) == "99"


# ---------------------------------------------------------------------------
# set_variable_with_mastership
# ---------------------------------------------------------------------------
# variables.py utilise post_mastership_domain_request / post_mastership_domain_release
# (POST /rw/mastership/{domain}) — signatures : (client, *, domain, action).


class TestSetVariableWithMastership:
    """Tests for set_variable_with_mastership()."""

    @pytest.mark.asyncio
    async def test_request_write_release_order(self, client: MagicMock) -> None:
        call_order: list[str] = []

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:request")
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:release")
            return _resp(status=204)

        async def fake_update(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            call_order.append("update")
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(f"{_MODULE}.update_rapid_variable_current_value", new=fake_update),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/x",
                value="42",
            )

        assert call_order == ["mastership:request", "update", "mastership:release"]

    @pytest.mark.asyncio
    async def test_release_called_even_on_error(self, client: MagicMock) -> None:
        """Mastership must be released even when the write raises."""
        released: list[bool] = []

        async def fake_update_fail(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            raise RWSHTTPError("write failed", status_code=403)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(f"{_MODULE}.update_rapid_variable_current_value", new=fake_update_fail),
            pytest.raises(RWSHTTPError),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/MainModule/x",
                value="42",
            )

        assert released == [True]

    @pytest.mark.asyncio
    async def test_update_called_with_correct_args(self, client: MagicMock) -> None:
        """update_rapid_variable_current_value must receive action='set'."""
        mock_update = AsyncMock(return_value=_resp(status=204))
        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.update_rapid_variable_current_value", new=mock_update),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/M/counter",
                value="99",
            )

        mock_update.assert_awaited_once_with(
            client,
            symbolurl="RAPID/T_ROB1/M/counter",
            action="set",
            value="99",
        )

    @pytest.mark.asyncio
    async def test_default_domain_is_rapid(self, client: MagicMock) -> None:
        """Default domain must be 'rapid'."""
        captured: dict[str, str] = {}

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            captured["domain"] = domain
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await set_variable_with_mastership(
                client,
                symbolurl="RAPID/T_ROB1/M/x",
                value="1",
            )

        assert captured["domain"] == "rapid"


# ---------------------------------------------------------------------------
# set_variables_with_mastership (batch write — previously untested)
# ---------------------------------------------------------------------------


class TestSetVariablesWithMastership:
    """Tests for set_variables_with_mastership()."""

    @pytest.mark.asyncio
    async def test_request_once_then_writes_all_then_release(
        self, client: MagicMock
    ) -> None:
        """Mastership must be requested/released exactly once, regardless
        of the number of variables written."""
        call_order: list[str] = []

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:request")
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:release")
            return _resp(status=204)

        async def fake_update(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            call_order.append(f"update:{symbolurl}")
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(f"{_MODULE}.update_rapid_variable_current_value", new=fake_update),
        ):
            await set_variables_with_mastership(
                client,
                values={
                    "RAPID/T_ROB1/M/x": "1",
                    "RAPID/T_ROB1/M/y": "2",
                },
            )

        assert call_order == [
            "mastership:request",
            "update:RAPID/T_ROB1/M/x",
            "update:RAPID/T_ROB1/M/y",
            "mastership:release",
        ]

    @pytest.mark.asyncio
    async def test_all_values_forwarded_correctly(self, client: MagicMock) -> None:
        """Each symbolurl/value pair must be forwarded with action='set'."""
        mock_update = AsyncMock(return_value=_resp(status=204))
        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.update_rapid_variable_current_value", new=mock_update),
        ):
            await set_variables_with_mastership(
                client,
                values={
                    "RAPID/T_ROB1/M/a": "10",
                    "RAPID/T_ROB1/M/b": "20",
                },
            )

        assert mock_update.await_count == 2
        mock_update.assert_any_await(
            client, symbolurl="RAPID/T_ROB1/M/a", action="set", value="10"
        )
        mock_update.assert_any_await(
            client, symbolurl="RAPID/T_ROB1/M/b", action="set", value="20"
        )

    @pytest.mark.asyncio
    async def test_release_called_even_if_one_write_fails(
        self, client: MagicMock
    ) -> None:
        """Mastership must be released even if a write in the middle of
        the batch raises."""
        released: list[bool] = []

        async def fake_update_fail_on_second(
            c: object,
            *,
            symbolurl: str,
            action: str,
            value: str,
        ) -> httpx.Response:
            if symbolurl == "RAPID/T_ROB1/M/b":
                raise RWSHTTPError("write failed", status_code=403)
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            released.append(True)
            return _resp(status=204)

        with (
            patch(
                f"{_MODULE}.post_mastership_domain_request",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=fake_update_fail_on_second,
            ),
            pytest.raises(RWSHTTPError),
        ):
            await set_variables_with_mastership(
                client,
                values={
                    "RAPID/T_ROB1/M/a": "1",
                    "RAPID/T_ROB1/M/b": "2",
                },
            )

        assert released == [True]

    @pytest.mark.asyncio
    async def test_empty_values_still_requests_and_releases(
        self, client: MagicMock
    ) -> None:
        """An empty values dict must still request/release mastership
        (no-op write loop) — no crash on empty input."""
        call_order: list[str] = []

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:request")
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            call_order.append("mastership:release")
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await set_variables_with_mastership(client, values={})

        assert call_order == ["mastership:request", "mastership:release"]

    @pytest.mark.asyncio
    async def test_default_domain_is_rapid(self, client: MagicMock) -> None:
        """Default domain must be 'rapid'."""
        captured: dict[str, str] = {}

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            captured["domain"] = domain
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(
                f"{_MODULE}.post_mastership_domain_release",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await set_variables_with_mastership(
                client,
                values={"RAPID/T_ROB1/M/x": "1"},
            )

        assert captured["domain"] == "rapid"

    @pytest.mark.asyncio
    async def test_custom_domain_forwarded(self, client: MagicMock) -> None:
        """A non-default domain must be forwarded to request/release/write."""
        captured: dict[str, str] = {}

        async def fake_request(c: object, *, domain: str, action: str) -> httpx.Response:
            captured["request_domain"] = domain
            return _resp(status=204)

        async def fake_release(c: object, *, domain: str, action: str) -> httpx.Response:
            captured["release_domain"] = domain
            return _resp(status=204)

        with (
            patch(f"{_MODULE}.post_mastership_domain_request", new=fake_request),
            patch(f"{_MODULE}.post_mastership_domain_release", new=fake_release),
            patch(
                f"{_MODULE}.update_rapid_variable_current_value",
                new=AsyncMock(return_value=_resp(status=204)),
            ),
        ):
            await set_variables_with_mastership(
                client,
                values={"RAPID/T_ROB1/M/x": "1"},
                domain="cfg",
            )

        assert captured["request_domain"] == "cfg"
        assert captured["release_domain"] == "cfg"


# ---------------------------------------------------------------------------
# get_variable
# ---------------------------------------------------------------------------


class TestGetVariable:
    """Tests for get_variable()."""

    @pytest.mark.asyncio
    async def test_returns_parsed_value(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.get_rapid_symbol_data",
            new=AsyncMock(return_value=_json_resp({"state": [{"value": "123"}]})),
        ):
            result = await get_variable(client, symbolurl="RAPID/T_ROB1/MainModule/counter")
        assert result == "123"

    @pytest.mark.asyncio
    async def test_passes_symbolurl(self, client: MagicMock) -> None:
        mock_get = AsyncMock(return_value=_json_resp({"state": [{"value": "TRUE"}]}))
        with patch(f"{_MODULE}.get_rapid_symbol_data", new=mock_get):
            await get_variable(client, symbolurl="RAPID/T_ROB1/M/flag")

        mock_get.assert_awaited_once_with(client, symbolurl="RAPID/T_ROB1/M/flag")

    @pytest.mark.asyncio
    async def test_returns_xml_value(self, client: MagicMock) -> None:
        with patch(
            f"{_MODULE}.get_rapid_symbol_data",
            new=AsyncMock(return_value=_resp('<span class="value">3.14</span>')),
        ):
            result = await get_variable(client, symbolurl="RAPID/T_ROB1/M/pi")
        assert result == "3.14"
