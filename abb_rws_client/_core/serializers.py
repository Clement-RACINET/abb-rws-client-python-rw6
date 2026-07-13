# abb_rws_client/_core/serializers.py
"""
Serialization / deserialization of RAPID types ↔ RWS format.

Author: Clement RACINET

RWS format for a robtarget (compact string, no spaces)::

    [[x,y,z],[q1,q2,q3,q4],[cf1,cf4,cf6,cfx],[eax_a,eax_b,eax_c,eax_d,eax_e,eax_f]]

ABB quaternion convention : [w, x, y, z]  (scalar first)
Inactive external axis     : 9E+9
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import TypeAlias

from abb_rws_client._core.exceptions import RWSValueError

#: ABB sentinel value for an inactive external axis
_INACTIVE_AXIS = 9e9
_INACTIVE_AXIS_STR = "9E+9"

_ROBTARGET_RE = re.compile(
    r"^\[\s*"
    r"\[([^\]]+)\]\s*,\s*"
    r"\[([^\]]+)\]\s*,\s*"
    r"\[([^\]]+)\]\s*,\s*"
    r"\[([^\]]+)\]\s*"
    r"\]\s*$"
)

#: Set of RAPID types supported by the serialization layer
_RAPID_TYPES = frozenset({"num", "bool", "string", "robtarget"})


@dataclass
class RobTarget:
    """Python representation of an ABB robtarget.

    Attributes:
        x: Cartesian X position (mm).
        y: Cartesian Y position (mm).
        z: Cartesian Z position (mm).
        qw: Orientation quaternion — scalar component (ABB convention: scalar first).
        qx: Orientation quaternion — X component.
        qy: Orientation quaternion — Y component.
        qz: Orientation quaternion — Z component.
        cf1: Robot configuration — axis 1 quadrant.
        cf4: Robot configuration — axis 4 quadrant.
        cf6: Robot configuration — axis 6 quadrant.
        cfx: Robot configuration — extended quadrant.
        eax: External axes (exactly 6 values; use ``9E+9`` for inactive axes).

    Raises:
        RWSValueError: If ``eax`` does not contain exactly 6 values.

    Example:
        ```python
        >>> rt = RobTarget(x=100.0, y=200.0, z=300.0)
        >>> rt.eax
        [9000000000.0, 9000000000.0, 9000000000.0, 9000000000.0, 9000000000.0, 9000000000.0]
        ```
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    qw: float = 1.0
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0
    cf1: float = 0.0
    cf4: float = 0.0
    cf6: float = 0.0
    cfx: float = 0.0
    eax: list[float] = field(default_factory=lambda: [_INACTIVE_AXIS] * 6)

    def __post_init__(self) -> None:
        if len(self.eax) != 6:
            raise RWSValueError(f"eax must have exactly 6 values, got {len(self.eax)}")


RapidValue: TypeAlias = float | bool | str | RobTarget


def _fmt(value: float) -> str:
    """Format a float for RWS: integer string if possible, compact repr otherwise.

    The inactive axis sentinel ``9E+9`` is always rendered as ``"9E+9"``
    regardless of the integer-check branch.

    Args:
        value: Float value to format.

    Returns:
        Compact string representation suitable for a RWS payload.

    Example:
        ```python
        >>> _fmt(100.0)
        '100'
        >>> _fmt(3.14)
        '3.14'
        >>> _fmt(9e9)
        '9E+9'
        ```
    """
    if value == _INACTIVE_AXIS:
        return _INACTIVE_AXIS_STR
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def _parse_floats(raw: str, expected: int, context: str) -> list[float]:
    """Parse a CSV string of floats with element count validation.

    Args:
        raw: Comma-separated string of float values (e.g. ``"0,0,500"``).
        expected: Expected number of elements.
        context: Label used in error messages to identify the field
            (e.g. ``"trans"``, ``"rot"``).

    Returns:
        List of parsed float values.

    Raises:
        RWSValueError: If the element count does not match ``expected``,
            or if any element cannot be converted to float.

    Example:
        ```python
        >>> _parse_floats("0,0,500", 3, "trans")
        [0.0, 0.0, 500.0]
        ```
    """
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != expected:
        raise RWSValueError(f"{context}: expected {expected} values, got {len(parts)} in {raw!r}")
    try:
        return [float(p) for p in parts]
    except ValueError as exc:
        raise RWSValueError(f"{context}: cannot parse float in {raw!r}") from exc


def robtarget_to_rws(rt: RobTarget) -> str:
    """Serialize a RobTarget into a compact RWS string.

    Route: ``PUT /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}``

    Args:
        rt: RobTarget instance to serialize.

    Returns:
        Compact RWS string with no spaces, e.g.:
        ``"[[100,200,300],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]"``

    Example:
        ```python
        >>> robtarget_to_rws(RobTarget(x=100.0, y=200.0, z=300.0))
        '[[100,200,300],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]'
        ```
    """
    trans = ",".join(_fmt(v) for v in (rt.x, rt.y, rt.z))
    rot = ",".join(_fmt(v) for v in (rt.qw, rt.qx, rt.qy, rt.qz))
    conf = ",".join(_fmt(v) for v in (rt.cf1, rt.cf4, rt.cf6, rt.cfx))
    ext = ",".join(_fmt(v) for v in rt.eax)
    return f"[[{trans}],[{rot}],[{conf}],[{ext}]]"


def rws_to_robtarget(raw: str) -> RobTarget:
    """Deserialize a raw RWS string into a RobTarget instance.

    Route: ``GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}``

    Args:
        raw: Raw RWS string returned by the controller.

    Returns:
        Populated RobTarget instance.

    Raises:
        RWSValueError: If the string format is invalid or any value
            cannot be parsed as a float.

    Example:
        ```python
        >>> rws_to_robtarget(
        ...     "[[0,0,500],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]"
        ... )
        RobTarget(x=0.0, y=0.0, z=500.0, ...)
        ```
    """
    m = _ROBTARGET_RE.match(raw.strip())
    if not m:
        raise RWSValueError(f"Invalid robtarget string: {raw!r}")
    trans = _parse_floats(m.group(1), 3, "trans")
    rot = _parse_floats(m.group(2), 4, "rot")
    conf = _parse_floats(m.group(3), 4, "conf")
    ext = _parse_floats(m.group(4), 6, "eax")
    return RobTarget(
        x=trans[0],
        y=trans[1],
        z=trans[2],
        qw=rot[0],
        qx=rot[1],
        qy=rot[2],
        qz=rot[3],
        cf1=conf[0],
        cf4=conf[1],
        cf6=conf[2],
        cfx=conf[3],
        eax=ext,
    )


def python_to_rapid_value(value: float | bool | str | RobTarget, rapid_type: str) -> str:
    """Convert a Python value to a RAPID string for the RWS API.

    Args:
        value: Python value to convert.
        rapid_type: Target RAPID type: ``"num"``, ``"bool"``,
            ``"string"``, or ``"robtarget"``.

    Returns:
        String in the format expected by RWS.

    Raises:
        RWSValueError: Unknown RAPID type, or value incompatible
            with the requested type.

    Example:
        ```python
        >>> python_to_rapid_value(3.14, "num")
        '3.14'
        >>> python_to_rapid_value(True, "bool")
        'TRUE'
        >>> python_to_rapid_value("hello", "string")
        'hello'
        ```
    """
    if rapid_type not in _RAPID_TYPES:
        raise RWSValueError(
            f"Unknown RAPID type: {rapid_type!r}. Expected one of {sorted(_RAPID_TYPES)}"
        )
    if rapid_type == "num":
        # bool is a subclass of int — must be rejected explicitly
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise RWSValueError(f"Expected int or float for 'num', got {type(value).__name__!r}")
        return str(int(value)) if float(value) == int(value) else repr(float(value))
    if rapid_type == "bool":
        if not isinstance(value, bool):
            raise RWSValueError(f"Expected bool for 'bool', got {type(value).__name__!r}")
        return "TRUE" if value else "FALSE"
    if rapid_type == "string":
        if not isinstance(value, str):
            raise RWSValueError(f"Expected str for 'string', got {type(value).__name__!r}")
        return value  # no quotes: RWS handles encoding on the form-data side
    if rapid_type == "robtarget":
        if not isinstance(value, RobTarget):
            raise RWSValueError(f"Expected RobTarget for 'robtarget', got {type(value).__name__!r}")
        return robtarget_to_rws(value)
    raise RWSValueError(f"Unknown RAPID type: {rapid_type!r}")  # unreachable — mypy guard


def rapid_value_to_python(raw: str, rapid_type: str) -> float | bool | str | RobTarget:
    """Convert a raw RWS string to a Python value according to the RAPID type.

    Args:
        raw: Raw string returned by the RWS controller.
        rapid_type: RAPID type: ``"num"``, ``"bool"``,
            ``"string"``, or ``"robtarget"``.

    Returns:
        Typed Python value.

    Raises:
        RWSValueError: Conversion failed or unknown RAPID type.

    Example:
        ```python
        >>> rapid_value_to_python("3.14", "num")
        3.14
        >>> rapid_value_to_python("TRUE", "bool")
        True
        >>> rapid_value_to_python("hello", "string")
        'hello'
        ```
    """
    if rapid_type not in _RAPID_TYPES:
        raise RWSValueError(
            f"Unknown RAPID type: {rapid_type!r}. Expected one of {sorted(_RAPID_TYPES)}"
        )
    if rapid_type == "num":
        try:
            return float(raw)
        except ValueError as exc:
            raise RWSValueError(f"Cannot convert {raw!r} to num") from exc
    if rapid_type == "bool":
        normalized = raw.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        raise RWSValueError(f"Cannot convert {raw!r} to bool")
    if rapid_type == "string":
        return raw  # raw passthrough, no quote stripping
    if rapid_type == "robtarget":
        return rws_to_robtarget(raw)
    raise RWSValueError(f"Unknown RAPID type: {rapid_type!r}")  # unreachable — mypy guard
