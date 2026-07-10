# tests/test_serializers.py
"""
Unit tests for abb_rws_client._core.serializers — no robot required.

Author: Clément RACINET

Coverage:
- robtarget_to_rws: serialization, float precision, sentinel values, no spaces
- rws_to_robtarget: deserialization, round-trip, error cases
- RobTarget dataclass: defaults, validation
- rapid_value_to_python: all supported RAPID types, error cases
- python_to_rapid_value: all supported RAPID types, type guards, error cases
"""

import pytest

from abb_rws_client._core.exceptions import RWSValueError
from abb_rws_client._core.serializers import (
    RapidValue,
    RobTarget,
    python_to_rapid_value,
    rapid_value_to_python,
    robtarget_to_rws,
    rws_to_robtarget,
)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

#: RWS string representation of a single inactive external axis
_INACTIVE = "9E+9"

#: RWS string representation of all six inactive external axes
_ALL_INACTIVE = f"[{_INACTIVE},{_INACTIVE},{_INACTIVE},{_INACTIVE},{_INACTIVE},{_INACTIVE}]"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def home_target() -> RobTarget:
    """Typical RobTarget: home position, identity quaternion, all axes inactive.

    Returns:
        A ``RobTarget`` at position (0, 0, 500) with identity orientation.
    """
    return RobTarget(x=0.0, y=0.0, z=500.0, qw=1.0, qx=0.0, qy=0.0, qz=0.0)


@pytest.fixture
def rws_home_str() -> str:
    """RWS string corresponding to ``home_target``.

    Returns:
        Compact RWS string for the home position.
    """
    return f"[[0,0,500],[1,0,0,0],[0,0,0,0],{_ALL_INACTIVE}]"


# ---------------------------------------------------------------------------
# robtarget_to_rws
# ---------------------------------------------------------------------------


class TestRobtargetToRws:
    def test_home_position(self, home_target: RobTarget, rws_home_str: str) -> None:
        """Home position must serialize to the expected compact RWS string."""
        assert robtarget_to_rws(home_target) == rws_home_str

    def test_float_precision_preserved(self) -> None:
        """Non-integer float values must be preserved in the serialized output."""
        rt = RobTarget(x=100.123, y=-200.456, z=0.001)
        result = robtarget_to_rws(rt)
        assert "100.123" in result
        assert "-200.456" in result
        assert "0.001" in result

    def test_inactive_axes_use_sentinel(self, home_target: RobTarget) -> None:
        """All six inactive external axes must be serialized as '9E+9'."""
        result = robtarget_to_rws(home_target)
        assert result.count(_INACTIVE) == 6

    def test_no_spaces_in_output(self) -> None:
        """The serialized RWS string must contain no whitespace characters."""
        rt = RobTarget(x=1.0, y=2.0, z=3.0)
        assert " " not in robtarget_to_rws(rt)

    def test_integer_floats_serialized_without_dot(self) -> None:
        """Float values equal to an integer must be serialized without a decimal point."""
        rt = RobTarget(x=100.0, y=200.0, z=300.0)
        result = robtarget_to_rws(rt)
        assert "100.0" not in result
        assert "100," in result or "100]" in result

    def test_custom_configuration(self) -> None:
        """Non-zero configuration values must appear correctly in the output."""
        rt = RobTarget(cf1=1.0, cf4=2.0, cf6=3.0, cfx=4.0)
        result = robtarget_to_rws(rt)
        assert "[1,2,3,4]" in result

    def test_partial_active_external_axes(self) -> None:
        """A mix of active and inactive external axes must serialize correctly."""
        rt = RobTarget(eax=[100.0, 9e9, 9e9, 9e9, 9e9, 9e9])
        result = robtarget_to_rws(rt)
        assert result.startswith("[[")
        assert "100" in result


# ---------------------------------------------------------------------------
# rws_to_robtarget
# ---------------------------------------------------------------------------


class TestRwsToRobtarget:
    def test_round_trip(self, home_target: RobTarget, rws_home_str: str) -> None:
        """Parsing the serialized home string must recover the original values."""
        parsed = rws_to_robtarget(rws_home_str)
        assert parsed.x == home_target.x
        assert parsed.y == home_target.y
        assert parsed.z == home_target.z
        assert parsed.qw == home_target.qw

    def test_inactive_axes_parsed_as_9e9(self, rws_home_str: str) -> None:
        """All inactive external axes must be parsed as 9e9."""
        parsed = rws_to_robtarget(rws_home_str)
        assert all(v == 9e9 for v in parsed.eax)

    def test_invalid_format_raises(self) -> None:
        """A string that does not match the robtarget pattern must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Invalid robtarget"):
            _ = rws_to_robtarget("not_a_robtarget")

    def test_wrong_number_of_trans_values(self) -> None:
        """Fewer than 3 translation values must raise RWSValueError mentioning 'trans'."""
        bad = f"[[1,2],[1,0,0,0],[0,0,0,0],{_ALL_INACTIVE}]"
        with pytest.raises(RWSValueError, match="trans"):
            _ = rws_to_robtarget(bad)

    def test_wrong_number_of_quat_values(self) -> None:
        """Fewer than 4 quaternion values must raise RWSValueError mentioning 'rot'."""
        bad = f"[[0,0,0],[1,0,0],[0,0,0,0],{_ALL_INACTIVE}]"
        with pytest.raises(RWSValueError, match="rot"):
            _ = rws_to_robtarget(bad)

    def test_non_numeric_value_raises(self) -> None:
        """A non-numeric token in the string must raise RWSValueError."""
        bad = f"[[0,0,abc],[1,0,0,0],[0,0,0,0],{_ALL_INACTIVE}]"
        with pytest.raises(RWSValueError, match="cannot parse float"):
            _ = rws_to_robtarget(bad)

    def test_spaces_in_input_tolerated(self) -> None:
        """Extra whitespace around brackets and values must be tolerated."""
        spaced = f"[ [0, 0, 500], [1, 0, 0, 0], [0, 0, 0, 0], {_ALL_INACTIVE} ]"
        parsed = rws_to_robtarget(spaced)
        assert parsed.z == 500.0

    def test_full_round_trip_with_floats(self) -> None:
        """Serializing then deserializing a RobTarget must preserve all float values."""
        rt = RobTarget(x=123.456, y=-78.9, z=1000.0, qw=0.707, qx=0.0, qy=0.707, qz=0.0)
        serialized = robtarget_to_rws(rt)
        parsed = rws_to_robtarget(serialized)
        assert abs(parsed.x - rt.x) < 1e-9
        assert abs(parsed.qw - rt.qw) < 1e-9


# ---------------------------------------------------------------------------
# RobTarget dataclass
# ---------------------------------------------------------------------------


class TestRobTargetDataclass:
    def test_default_quaternion_is_identity(self) -> None:
        """Default quaternion must be the identity (qw=1, qx=qy=qz=0)."""
        rt = RobTarget()
        assert rt.qw == 1.0
        assert rt.qx == rt.qy == rt.qz == 0.0

    def test_default_eax_has_six_elements(self) -> None:
        """Default external axes list must contain exactly 6 elements."""
        rt = RobTarget()
        assert len(rt.eax) == 6

    def test_invalid_eax_length_raises(self) -> None:
        """Providing fewer than 6 external axis values must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="eax must have exactly 6"):
            _ = RobTarget(eax=[1.0, 2.0])


# ---------------------------------------------------------------------------
# rapid_value_to_python
# ---------------------------------------------------------------------------


class TestRapidValueToPython:
    def test_num_integer(self) -> None:
        """An integer string must be parsed as a float."""
        result: RapidValue = rapid_value_to_python("42", "num")
        assert result == 42.0

    def test_num_float(self) -> None:
        """A decimal string must be parsed as a float with correct precision."""
        result: RapidValue = rapid_value_to_python("3.14", "num")
        assert isinstance(result, float)
        assert abs(result - 3.14) < 1e-9

    def test_num_invalid_raises(self) -> None:
        """A non-numeric string for type 'num' must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Cannot convert"):
            _ = rapid_value_to_python("abc", "num")

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("true", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
        ],
    )
    def test_bool_variants(self, raw: str, expected: bool) -> None:
        """All recognised boolean string variants must parse to the correct bool."""
        assert rapid_value_to_python(raw, "bool") is expected

    def test_bool_invalid_raises(self) -> None:
        """An unrecognised string for type 'bool' must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Cannot convert"):
            _ = rapid_value_to_python("maybe", "bool")

    def test_string_passthrough(self) -> None:
        """A string value must be returned as-is without modification."""
        assert rapid_value_to_python("hello world", "string") == "hello world"

    def test_robtarget_returns_robtarget_instance(self) -> None:
        """A valid robtarget RWS string must be parsed into a RobTarget instance."""
        rws = f"[[0,0,500],[1,0,0,0],[0,0,0,0],{_ALL_INACTIVE}]"
        result = rapid_value_to_python(rws, "robtarget")
        assert isinstance(result, RobTarget)

    def test_unknown_type_raises(self) -> None:
        """An unsupported RAPID type must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Unknown RAPID type"):
            _ = rapid_value_to_python("x", "pose")


# ---------------------------------------------------------------------------
# python_to_rapid_value
# ---------------------------------------------------------------------------


class TestPythonToRapidValue:
    def test_num_int(self) -> None:
        """An integer value for type 'num' must serialize without a decimal point."""
        assert python_to_rapid_value(42, "num") == "42"

    def test_num_float(self) -> None:
        """A non-integer float for type 'num' must serialize using repr()."""
        assert python_to_rapid_value(3.14, "num") == repr(3.14)

    def test_num_wrong_type_raises(self) -> None:
        """Passing a string for type 'num' must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Expected int or float"):
            _ = python_to_rapid_value("42", "num")

    def test_bool_is_rejected_as_num(self) -> None:
        """bool is a subclass of int and must be explicitly rejected for type 'num'."""
        with pytest.raises(RWSValueError, match="Expected int or float"):
            _ = python_to_rapid_value(True, "num")

    def test_bool_true(self) -> None:
        """Python True must serialize to the RAPID string 'TRUE'."""
        assert python_to_rapid_value(True, "bool") == "TRUE"

    def test_bool_false(self) -> None:
        """Python False must serialize to the RAPID string 'FALSE'."""
        assert python_to_rapid_value(False, "bool") == "FALSE"

    def test_bool_wrong_type_raises(self) -> None:
        """Passing a non-bool value for type 'bool' must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Expected bool"):
            _ = python_to_rapid_value(1, "bool")

    def test_string_conversion(self) -> None:
        """A string value for type 'string' must be returned as-is."""
        assert python_to_rapid_value("hello", "string") == "hello"

    def test_robtarget_serialized(self, home_target: RobTarget, rws_home_str: str) -> None:
        """A RobTarget must serialize to the expected compact RWS string."""
        assert python_to_rapid_value(home_target, "robtarget") == rws_home_str

    def test_robtarget_wrong_type_raises(self) -> None:
        """Passing a non-RobTarget value for type 'robtarget' must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Expected RobTarget"):
            _ = python_to_rapid_value("not_a_robtarget", "robtarget")

    def test_unknown_type_raises(self) -> None:
        """An unsupported RAPID type must raise RWSValueError."""
        with pytest.raises(RWSValueError, match="Unknown RAPID type"):
            _ = python_to_rapid_value(1, "pose")
