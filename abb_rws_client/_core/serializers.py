# abb_rws_client/_core/serializers.py
"""
Sérialisation / désérialisation des types RAPID ↔ format RWS.

Format RWS d'un robtarget (string compacte, sans espaces) :
    [[x,y,z],[q1,q2,q3,q4],[cf1,cf4,cf6,cfx],[eax_a,eax_b,eax_c,eax_d,eax_e,eax_f]]

Convention ABB quaternion : [w, x, y, z]  (scalaire en premier)
Axe externe inactif       : 9E+9
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TypeAlias

from abb_rws_client._core.exceptions import RWSValueError

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

_RAPID_TYPES = frozenset({"num", "bool", "string", "robtarget"})


@dataclass
class RobTarget:
    """Représentation Python d'un robtarget ABB.

    Attributes:
        x, y, z: Position cartésienne (mm).
        qw, qx, qy, qz: Quaternion d'orientation (convention ABB : scalaire en premier).
        cf1, cf4, cf6, cfx: Configuration du robot (quadrant).
        eax: Axes externes (6 valeurs ; 9E+9 = inactif).
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
    """Formate un float pour RWS : entier si possible, sinon repr compacte."""
    if value == _INACTIVE_AXIS:
        return _INACTIVE_AXIS_STR
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def _parse_floats(raw: str, expected: int, context: str) -> list[float]:
    """Parse une chaîne CSV de floats avec validation du nombre d'éléments."""
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != expected:
        raise RWSValueError(
            f"{context}: expected {expected} values, got {len(parts)} in {raw!r}"
        )
    try:
        return [float(p) for p in parts]
    except ValueError as exc:
        raise RWSValueError(f"{context}: cannot parse float in {raw!r}") from exc


def robtarget_to_rws(rt: RobTarget) -> str:
    """Sérialise un RobTarget en string RWS compacte.

    Route : PUT /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}

    Args:
        rt: Instance RobTarget à sérialiser.

    Returns:
        String RWS compacte sans espaces, ex:
        ``"[[100,200,300],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]"``

    Example:
        >>> robtarget_to_rws(RobTarget(x=100.0, y=200.0, z=300.0))
        '[[100,200,300],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]'
    """
    trans = ",".join(_fmt(v) for v in (rt.x, rt.y, rt.z))
    rot = ",".join(_fmt(v) for v in (rt.qw, rt.qx, rt.qy, rt.qz))
    conf = ",".join(_fmt(v) for v in (rt.cf1, rt.cf4, rt.cf6, rt.cfx))
    ext = ",".join(_fmt(v) for v in rt.eax)
    return f"[[{trans}],[{rot}],[{conf}],[{ext}]]"


def rws_to_robtarget(raw: str) -> RobTarget:
    """Désérialise une string RWS en RobTarget.

    Route : GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}

    Args:
        raw: String RWS brute retournée par le contrôleur.

    Returns:
        Instance RobTarget peuplée.

    Raises:
        RWSValueError: Si le format est invalide ou les valeurs non parsables.

    Example:
        >>> rws_to_robtarget("[[0,0,500],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]")
        RobTarget(x=0.0, y=0.0, z=500.0, ...)
    """
    m = _ROBTARGET_RE.match(raw.strip())
    if not m:
        raise RWSValueError(f"Invalid robtarget string: {raw!r}")
    trans = _parse_floats(m.group(1), 3, "trans")
    rot = _parse_floats(m.group(2), 4, "rot")
    conf = _parse_floats(m.group(3), 4, "conf")
    ext = _parse_floats(m.group(4), 6, "eax")
    return RobTarget(
        x=trans[0], y=trans[1], z=trans[2],
        qw=rot[0], qx=rot[1], qy=rot[2], qz=rot[3],
        cf1=conf[0], cf4=conf[1], cf6=conf[2], cfx=conf[3],
        eax=ext,
    )


def python_to_rapid_value(value: float | bool | str | RobTarget, rapid_type: str) -> str:
    """Convertit une valeur Python en string RAPID pour l'API RWS.

    Args:
        value: Valeur Python à convertir.
        rapid_type: Type RAPID cible : ``"num"``, ``"bool"``, ``"string"``, ``"robtarget"``.

    Returns:
        String au format attendu par RWS.

    Raises:
        RWSValueError: Type RAPID inconnu, ou valeur incompatible avec le type.

    Example:
        >>> python_to_rapid_value(3.14, "num")
        '3.14'
        >>> python_to_rapid_value(True, "bool")
        'TRUE'
        >>> python_to_rapid_value("hello", "string")
        'hello'
    """
    if rapid_type not in _RAPID_TYPES:
        raise RWSValueError(
            f"Unknown RAPID type: {rapid_type!r}. Expected one of {sorted(_RAPID_TYPES)}"
        )
    if rapid_type == "num":
        # bool est sous-classe de int — doit être rejeté explicitement
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise RWSValueError(
                f"Expected int or float for 'num', got {type(value).__name__!r}"
            )
        return str(int(value)) if float(value) == int(value) else repr(float(value))
    if rapid_type == "bool":
        if not isinstance(value, bool):
            raise RWSValueError(
                f"Expected bool for 'bool', got {type(value).__name__!r}"
            )
        return "TRUE" if value else "FALSE"
    if rapid_type == "string":
        if not isinstance(value, str):
            raise RWSValueError(
                f"Expected str for 'string', got {type(value).__name__!r}"
            )
        return value  # ← pas de guillemets : RWS gère l'encodage côté form-data
    if rapid_type == "robtarget":
        if not isinstance(value, RobTarget):
            raise RWSValueError(
                f"Expected RobTarget for 'robtarget', got {type(value).__name__!r}"
            )
        return robtarget_to_rws(value)
    raise RWSValueError(f"Unknown RAPID type: {rapid_type!r}")  # unreachable, mypy


def rapid_value_to_python(raw: str, rapid_type: str) -> float | bool | str | RobTarget:
    """Convertit une string RWS en valeur Python selon le type RAPID.

    Args:
        raw: String brute retournée par le contrôleur RWS.
        rapid_type: Type RAPID : ``"num"``, ``"bool"``, ``"string"``, ``"robtarget"``.

    Returns:
        Valeur Python typée.

    Raises:
        RWSValueError: Conversion impossible ou type inconnu.

    Example:
        >>> rapid_value_to_python("3.14", "num")
        3.14
        >>> rapid_value_to_python("TRUE", "bool")
        True
        >>> rapid_value_to_python("hello", "string")
        'hello'
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
        return raw  # ← passthrough brut, sans strip de guillemets
    if rapid_type == "robtarget":
        return rws_to_robtarget(raw)
    raise RWSValueError(f"Unknown RAPID type: {rapid_type!r}")  # unreachable, mypy