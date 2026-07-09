# tests/test_rapid_variable.py
"""
Tests unitaires pour rapid_variable.py — aucun robot requis.

Stratégie :
    - serialize/deserialize : tests purs, pas de réseau
    - get_rapid_var / set_rapid_var : mock httpx transport
    - Cas limites : arrays vides, types incorrects, structure JSON inattendue
"""

from __future__ import annotations

import json

import httpx
import pytest

from old_abb_rws_client.client import RWSClient
from old_abb_rws_client.exceptions import RWSValueError
from old_abb_rws_client.rapid_variable import (
    DEFAULT_TASK,
    RAPID_TYPES,
    build_symbol_path,
    deserialize_rapid_value,
    extract_lvalue,
    get_rapid_var,
    serialize_rapid_value,
    set_rapid_var,
)
from old_abb_rws_client.serializers import RobTarget

# ---------------------------------------------------------------------------
# Helpers mock
# ---------------------------------------------------------------------------


def _resp(status_code: int, body: dict | None = None) -> httpx.Response:  # type: ignore[type-arg]
    content = json.dumps(body).encode() if body else b""
    return httpx.Response(status_code=status_code, content=content)


def _rws_var_response(lvalue: str) -> dict:  # type: ignore[type-arg]
    """Simule la structure JSON retournée par GET /rw/rapid/symbol/data/...?json=1"""
    return {"state": [{"lvalue": lvalue}]}


class _RouteTransport(httpx.AsyncBaseTransport):
    """Transport mock : route les requêtes vers des réponses prédéfinies par path."""

    def __init__(self, routes: dict[str, httpx.Response]) -> None:  # type: ignore[type-arg]
        self._routes = routes
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.lstrip("/")
        return self._routes.get(path, _resp(404))


async def _make_client(transport: httpx.AsyncBaseTransport) -> RWSClient:
    """Crée un RWSClient avec transport mock injecté directement."""
    client = RWSClient(host="192.168.125.1")
    client._http = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


# ---------------------------------------------------------------------------
# build_symbol_path
# ---------------------------------------------------------------------------


class TestBuildSymbolPath:
    def test_standard(self) -> None:
        path = build_symbol_path("SPEED", "MYMOD", "T_ROB1")
        assert path == "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/SPEED"

    def test_custom_task(self) -> None:
        assert "T_ROB2" in build_symbol_path("VAR", "MOD", "T_ROB2")

    def test_no_leading_slash(self) -> None:
        assert not build_symbol_path("VAR", "MOD", "T_ROB1").startswith("/")

    def test_default_task_is_t_rob1(self) -> None:
        assert DEFAULT_TASK == "T_ROB1"


# ---------------------------------------------------------------------------
# serialize_rapid_value — scalaires (délégués à serializers.py)
# ---------------------------------------------------------------------------


class TestSerializeNum:
    def test_float(self) -> None:
        assert serialize_rapid_value(3.14, "num") == "3.14"

    def test_int_converted(self) -> None:
        assert serialize_rapid_value(42, "num") == "42"

    def test_zero(self) -> None:
        assert serialize_rapid_value(0.0, "num") == "0"

    def test_negative(self) -> None:
        assert serialize_rapid_value(-1.5, "num") == "-1.5"

    def test_bool_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value(True, "num")

    def test_string_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value("3.14", "num")


class TestSerializeBool:
    def test_true(self) -> None:
        assert serialize_rapid_value(True, "bool") == "TRUE"

    def test_false(self) -> None:
        assert serialize_rapid_value(False, "bool") == "FALSE"

    def test_int_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value(1, "bool")


class TestSerializeString:
    def test_simple(self) -> None:
        assert serialize_rapid_value("hello", "string") == "hello"

    def test_empty(self) -> None:
        assert serialize_rapid_value("", "string") == ""

    def test_filename(self) -> None:
        assert serialize_rapid_value("part_A.prg", "string") == "part_A.prg"


# ---------------------------------------------------------------------------
# serialize_rapid_value — arrays
# ---------------------------------------------------------------------------


class TestSerializeNumArray:
    def test_basic(self) -> None:
        assert serialize_rapid_value([1.0, 2.0, 3.0], "num[]") == "[1.0,2.0,3.0]"

    def test_empty(self) -> None:
        assert serialize_rapid_value([], "num[]") == "[]"

    def test_ints_converted(self) -> None:
        assert serialize_rapid_value([1, 2, 3], "num[]") == "[1.0,2.0,3.0]"

    def test_no_spaces(self) -> None:
        assert " " not in serialize_rapid_value([1.0, 2.0], "num[]")

    def test_bool_in_list_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value([True, False], "num[]")

    def test_not_a_list_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value(42.0, "num[]")


class TestSerializeBoolArray:
    def test_basic(self) -> None:
        assert serialize_rapid_value([True, False, True], "bool[]") == "[TRUE,FALSE,TRUE]"

    def test_empty(self) -> None:
        assert serialize_rapid_value([], "bool[]") == "[]"

    def test_int_in_list_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value([1, 0], "bool[]")

    def test_not_a_list_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value(True, "bool[]")


class TestSerializeStringArray:
    def test_basic(self) -> None:
        assert serialize_rapid_value(["a", "b", "c"], "string[]") == '["a","b","c"]'

    def test_empty(self) -> None:
        assert serialize_rapid_value([], "string[]") == "[]"

    def test_filenames(self) -> None:
        result = serialize_rapid_value(["part_A.prg", "part_B.prg"], "string[]")
        assert result == '["part_A.prg","part_B.prg"]'

    def test_int_in_list_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value([1, 2], "string[]")

    def test_not_a_list_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value("hello", "string[]")


# ---------------------------------------------------------------------------
# serialize_rapid_value — robtarget (délégué à serializers.py)
# ---------------------------------------------------------------------------


class TestSerializeRobtarget:
    def test_valid(self) -> None:
        rt = RobTarget(x=100.0, y=200.0, z=300.0, qw=1.0)
        result = serialize_rapid_value(rt, "robtarget")
        assert result.startswith("[[")
        assert "100" in result

    def test_non_robtarget_rejected(self) -> None:
        with pytest.raises(RWSValueError):
            serialize_rapid_value([100.0, 200.0, 300.0], "robtarget")


# ---------------------------------------------------------------------------
# serialize_rapid_value — type inconnu
# ---------------------------------------------------------------------------


class TestSerializeUnknownType:
    def test_unknown_raises(self) -> None:
        with pytest.raises(RWSValueError, match="Unknown RAPID type"):
            serialize_rapid_value(42.0, "dnum")

    def test_all_known_types_dont_raise_unknown(self) -> None:
        for t in RAPID_TYPES:
            try:
                serialize_rapid_value(0.0, t)
            except RWSValueError as e:
                assert "Unknown RAPID type" not in str(e)


# ---------------------------------------------------------------------------
# deserialize_rapid_value — scalaires
# ---------------------------------------------------------------------------


class TestDeserializeNum:
    def test_float_string(self) -> None:
        assert deserialize_rapid_value("3.14", "num") == pytest.approx(3.14)

    def test_integer_string(self) -> None:
        assert deserialize_rapid_value("42", "num") == pytest.approx(42.0)

    def test_negative(self) -> None:
        assert deserialize_rapid_value("-1.5", "num") == pytest.approx(-1.5)

    def test_invalid_raises(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value("not_a_number", "num")


class TestDeserializeBool:
    def test_true(self) -> None:
        assert deserialize_rapid_value("TRUE", "bool") is True

    def test_false(self) -> None:
        assert deserialize_rapid_value("FALSE", "bool") is False

    def test_lowercase_robust(self) -> None:
        # serializers.rapid_value_to_python accepte "true"/"false"
        assert deserialize_rapid_value("true", "bool") is True


class TestDeserializeString:
    def test_simple(self) -> None:
        assert deserialize_rapid_value("hello", "string") == "hello"

    def test_empty(self) -> None:
        assert deserialize_rapid_value("", "string") == ""


# ---------------------------------------------------------------------------
# deserialize_rapid_value — arrays
# ---------------------------------------------------------------------------


class TestDeserializeNumArray:
    def test_basic(self) -> None:
        result = deserialize_rapid_value("[1.0,2.0,3.0]", "num[]")
        assert result == pytest.approx([1.0, 2.0, 3.0])

    def test_empty(self) -> None:
        assert deserialize_rapid_value("[]", "num[]") == []

    def test_invalid_format_no_brackets(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value("1.0,2.0", "num[]")

    def test_non_numeric_element(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value("[1.0,abc]", "num[]")


class TestDeserializeBoolArray:
    def test_basic(self) -> None:
        assert deserialize_rapid_value("[TRUE,FALSE,TRUE]", "bool[]") == [True, False, True]

    def test_empty(self) -> None:
        assert deserialize_rapid_value("[]", "bool[]") == []

    def test_invalid_token(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value("[TRUE,MAYBE]", "bool[]")

    def test_invalid_format_no_brackets(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value("TRUE,FALSE", "bool[]")


class TestDeserializeStringArray:
    def test_basic(self) -> None:
        assert deserialize_rapid_value('["a","b","c"]', "string[]") == ["a", "b", "c"]

    def test_empty(self) -> None:
        assert deserialize_rapid_value("[]", "string[]") == []

    def test_filenames(self) -> None:
        result = deserialize_rapid_value('["part_A.prg","part_B.prg"]', "string[]")
        assert result == ["part_A.prg", "part_B.prg"]

    def test_invalid_json(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value('["a","b"', "string[]")

    def test_invalid_format_no_brackets(self) -> None:
        with pytest.raises(RWSValueError):
            deserialize_rapid_value('"a","b"', "string[]")


# ---------------------------------------------------------------------------
# extract_lvalue
# ---------------------------------------------------------------------------


class TestExtractLvalue:
    def test_valid(self) -> None:
        assert extract_lvalue({"state": [{"lvalue": "42.0"}]}) == "42.0"

    def test_missing_state_key(self) -> None:
        with pytest.raises(RWSValueError):
            extract_lvalue({})

    def test_empty_state_list(self) -> None:
        with pytest.raises(RWSValueError):
            extract_lvalue({"state": []})

    def test_missing_lvalue_key(self) -> None:
        with pytest.raises(RWSValueError):
            extract_lvalue({"state": [{"other": "x"}]})


# ---------------------------------------------------------------------------
# get_rapid_var — intégration mock HTTP
# ---------------------------------------------------------------------------


class TestGetRapidVar:
    async def test_get_num(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/SPEED"
        transport = _RouteTransport({path: _resp(200, _rws_var_response("150.0"))})
        client = await _make_client(transport)
        result = await get_rapid_var(client, "SPEED", "num", module="MYMOD")
        assert result == pytest.approx(150.0)

    async def test_get_bool(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/ACTIVE"
        transport = _RouteTransport({path: _resp(200, _rws_var_response("TRUE"))})
        client = await _make_client(transport)
        result = await get_rapid_var(client, "ACTIVE", "bool", module="MYMOD")
        assert result is True

    async def test_get_string_array(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/FILES"
        transport = _RouteTransport({
            path: _resp(200, _rws_var_response('["a.prg","b.prg"]'))
        })
        client = await _make_client(transport)
        result = await get_rapid_var(client, "FILES", "string[]", module="MYMOD")
        assert result == ["a.prg", "b.prg"]

    async def test_json_query_param_sent(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/SPEED"
        transport = _RouteTransport({path: _resp(200, _rws_var_response("1.0"))})
        client = await _make_client(transport)
        await get_rapid_var(client, "SPEED", "num", module="MYMOD")
        assert "json=1" in str(transport.requests[0].url)

    async def test_get_custom_task(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB2/MYMOD/VAR"
        transport = _RouteTransport({path: _resp(200, _rws_var_response("1.0"))})
        client = await _make_client(transport)
        result = await get_rapid_var(client, "VAR", "num", module="MYMOD", task="T_ROB2")
        assert result == pytest.approx(1.0)

    async def test_invalid_json_response_raises(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/SPEED"
        transport = _RouteTransport({path: httpx.Response(200, content=b"not json")})
        client = await _make_client(transport)
        with pytest.raises(RWSValueError, match="JSON"):
            await get_rapid_var(client, "SPEED", "num", module="MYMOD")


# ---------------------------------------------------------------------------
# set_rapid_var — intégration mock HTTP
# ---------------------------------------------------------------------------


class TestSetRapidVar:
    async def test_set_num(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/SPEED"
        transport = _RouteTransport({path: _resp(204)})
        client = await _make_client(transport)
        await set_rapid_var(client, "SPEED", 150.0, "num", module="MYMOD")
        req = transport.requests[0]
        assert req.method == "PUT"
        assert b"value=150" in req.content

    async def test_set_bool_true(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/ACTIVE"
        transport = _RouteTransport({path: _resp(204)})
        client = await _make_client(transport)
        await set_rapid_var(client, "ACTIVE", True, "bool", module="MYMOD")
        assert b"value=TRUE" in transport.requests[0].content

    async def test_set_string_array(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB1/MYMOD/FILES"
        transport = _RouteTransport({path: _resp(204)})
        client = await _make_client(transport)
        await set_rapid_var(client, "FILES", ["a.prg", "b.prg"], "string[]", module="MYMOD")
        body = transport.requests[0].content.decode()
        assert "a.prg" in body
        assert "b.prg" in body

    async def test_invalid_value_raises_before_request(self) -> None:
        """La sérialisation échoue avant toute requête réseau."""
        transport = _RouteTransport({})
        client = await _make_client(transport)
        with pytest.raises(RWSValueError):
            await set_rapid_var(client, "SPEED", "not_a_float", "num", module="MYMOD")
        assert len(transport.requests) == 0

    async def test_set_custom_task(self) -> None:
        path = "rw/rapid/symbol/data/RAPID/T_ROB2/MYMOD/VAR"
        transport = _RouteTransport({path: _resp(204)})
        client = await _make_client(transport)
        await set_rapid_var(client, "VAR", 1.0, "num", module="MYMOD", task="T_ROB2")
        assert "/T_ROB2/" in transport.requests[0].url.path


class TestDeserializeStringArrayEdgeCases:
    def test_mixed_types_in_json_array_rejected(self) -> None:
        """[1, "b"] est du JSON valide mais pas un list[str] — doit lever RWSValueError."""
        with pytest.raises(RWSValueError, match="mixed types"):
            deserialize_rapid_value('[1, "b"]', "string[]")


class TestUnknownTypeInDeserialize:
    def test_unknown_type_raises(self) -> None:
        with pytest.raises(RWSValueError, match="Unknown RAPID type"):
            deserialize_rapid_value("42", "dnum")