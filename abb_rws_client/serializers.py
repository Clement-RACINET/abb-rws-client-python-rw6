# abb_rws_client/serializers.py
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

from abb_rws_client.exceptions import RWSValueError

# Valeur sentinelle ABB pour un axe externe inactif
_INACTIVE_AXIS = 9e9
_INACTIVE_AXIS_STR = "9E+9"

# Regex pour valider / extraire les 4 groupes d'un robtarget RWS
_ROBTARGET_RE = re.compile(
    r"^\[\s*"
    r"\[([^\]]+)\]\s*,\s*"
    r"\[([^\]]+)\]\s*,\s*"
    r"\[([^\]]+)\]\s*,\s*"
    r"\[([^\]]+)\]\s*"
    r"\]\s*$"
)


# ---------------------------------------------------------------------------
# Dataclass RobTarget
# ---------------------------------------------------------------------------


@dataclass
class RobTarget:
    """Représentation Python d'un robtarget ABB.

    Attributes:
        x, y, z: Position cartésienne (mm).
        qw, qx, qy, qz: Quaternion d'orientation (convention ABB : scalaire en premier).
        cf1, cf4, cf6, cfx: Configuration du robot (quadrant).
        eax: Axes externes (6 valeurs ; 9E+9 = inactif).
    """

    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Orientation (quaternion ABB : w, x, y, z)
    qw: float = 1.0
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0

    # Configuration
    cf1: float = 0.0
    cf4: float = 0.0
    cf6: float = 0.0
    cfx: float = 0.0

    # Axes externes (6 axes, inactifs par défaut)
    eax: list[float] = field(default_factory=lambda: [_INACTIVE_AXIS] * 6)

    def __post_init__(self) -> None:
        if len(self.eax) != 6:
            raise RWSValueError(f"eax must have exactly 6 values, got {len(self.eax)}")


# ---------------------------------------------------------------------------
# Type alias — défini APRÈS RobTarget pour éviter la forward reference
# ---------------------------------------------------------------------------

# Type union pour toutes les valeurs RAPID supportées par ce client
RapidValue: TypeAlias = float | bool | str | RobTarget


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------


def robtarget_to_rws(rt: RobTarget) -> str:
    """Sérialise un RobTarget en string RWS compacte.

    Example:
        >>> rt = RobTarget(x=100.0, y=200.5, z=300.0, qw=1.0)
        >>> robtarget_to_rws(rt)
        '[[100,200.5,300],[1,0,0,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]'
    """
    trans = f"[{_fmt(rt.x)},{_fmt(rt.y)},{_fmt(rt.z)}]"
    rot = f"[{_fmt(rt.qw)},{_fmt(rt.qx)},{_fmt(rt.qy)},{_fmt(rt.qz)}]"
    conf = f"[{_fmt(rt.cf1)},{_fmt(rt.cf4)},{_fmt(rt.cf6)},{_fmt(rt.cfx)}]"
    ext = f"[{','.join(_fmt(v) for v in rt.eax)}]"
    return f"[{trans},{rot},{conf},{ext}]"


def rws_to_robtarget(rws_str: str) -> RobTarget:
    """Désérialise une string RWS en RobTarget.

    Args:
        rws_str: String au format RWS, telle que retournée par GET /rw/rapid/symbol/data/...

    Raises:
        RWSValueError: Si le format est invalide ou les valeurs non parsables.
    """
    match = _ROBTARGET_RE.match(rws_str.strip())
    if not match:
        raise RWSValueError(f"Invalid robtarget RWS format: {rws_str!r}")

    trans_raw, rot_raw, conf_raw, ext_raw = match.groups()

    trans = _parse_floats(trans_raw, 3, "trans[x,y,z]")
    rot = _parse_floats(rot_raw, 4, "rot[qw,qx,qy,qz]")
    conf = _parse_floats(conf_raw, 4, "robconf[cf1,cf4,cf6,cfx]")
    ext = _parse_floats(ext_raw, 6, "extax[eax_a..eax_f]")

    return RobTarget(
        x=trans[0], y=trans[1], z=trans[2],
        qw=rot[0], qx=rot[1], qy=rot[2], qz=rot[3],
        cf1=conf[0], cf4=conf[1], cf6=conf[2], cfx=conf[3],
        eax=ext,
    )


def rapid_value_to_python(raw: str, rapid_type: str) -> RapidValue:
    """Convertit une valeur brute RWS vers le type Python correspondant.

    Args:
        raw: Valeur brute retournée par RWS (toujours une string).
        rapid_type: Type RAPID déclaré : "num" | "bool" | "string" | "robtarget".

    Raises:
        RWSValueError: Type inconnu ou valeur non convertible.
    """
    match rapid_type:
        case "num":
            try:
                return float(raw)
            except ValueError as exc:
                raise RWSValueError(f"Cannot convert {raw!r} to num") from exc
        case "bool":
            low = raw.strip().lower()
            if low in ("true", "1", "yes"):
                return True
            if low in ("false", "0", "no"):
                return False
            raise RWSValueError(f"Cannot convert {raw!r} to bool")
        case "string":
            return raw
        case "robtarget":
            return rws_to_robtarget(raw)
        case _:
            raise RWSValueError(f"Unknown RAPID type: {rapid_type!r}")


def python_to_rapid_value(value: RapidValue, rapid_type: str) -> str:
    """Convertit une valeur Python en string RWS pour un PUT.

    Args:
        value: Valeur Python à envoyer (float, bool, str ou RobTarget).
        rapid_type: Type RAPID cible : "num" | "bool" | "string" | "robtarget".

    Raises:
        RWSValueError: Type inconnu ou valeur non sérialisable.
    """
    match rapid_type:
        case "num":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise RWSValueError(
                    f"Expected int or float for num, got {type(value).__name__}"
                )
            return _fmt(float(value))
        case "bool":
            if not isinstance(value, bool):
                raise RWSValueError(f"Expected bool, got {type(value).__name__}")
            return "TRUE" if value else "FALSE"
        case "string":
            return str(value)
        case "robtarget":
            if not isinstance(value, RobTarget):
                raise RWSValueError(f"Expected RobTarget, got {type(value).__name__}")
            return robtarget_to_rws(value)
        case _:
            raise RWSValueError(f"Unknown RAPID type: {rapid_type!r}")
