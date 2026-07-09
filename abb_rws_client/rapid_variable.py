# abb_rws_client/rapid_variable.py
"""
Lecture et écriture de variables RAPID sur un contrôleur ABB RobotWare 6.

Routes RWS (cf. arbre /rw/rapid) :
    Lecture  : GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{var}?json=1
    Écriture : PUT /rw/rapid/symbol/data/RAPID/{task}/{module}/{var}
               Body : value=<valeur>   (application/x-www-form-urlencoded)

Réponse JSON RWS (lecture) :
    { "state": [ { "lvalue": "<valeur brute>" } ] }

Types RAPID supportés :
    Scalaires  → num, bool, string, robtarget  (délégués à serializers.py)
    Tableaux   → num[], bool[], string[]        (gérés ici)

Ce module est entièrement générique : aucune valeur par défaut applicative
(module, task) n'est codée en dur. `module` est un paramètre obligatoire.
Seul `task="T_ROB1"` est proposé comme défaut car c'est la convention ABB
universelle pour un robot single-arm sous RW6.

⚠️  Toute écriture doit être effectuée sous Mastership :
    async with Mastership(client):
        await set_rapid_var(client, "SPEED", 100.0, "num", module="MYMOD")
"""

from __future__ import annotations

import json as _json
import logging
from typing import TYPE_CHECKING

from abb_rws_client.exceptions import RWSValueError
from abb_rws_client.serializers import (
    RobTarget,
    python_to_rapid_value,
    rapid_value_to_python,
)

if TYPE_CHECKING:
    from abb_rws_client.client import RWSClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

#: Tâche RAPID par défaut — T_ROB1 est la convention ABB pour un robot single-arm.
#: Surcharger via le paramètre `task` pour les configurations multi-tâches.
DEFAULT_TASK: str = "T_ROB1"

#: Préfixe de chemin RWS pour les symboles RAPID
#: Correspond à la branche /rw → /rapid → /symbol → /data de l'arbre RWS
_SYMBOL_BASE: str = "rw/rapid/symbol/data/RAPID"

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

#: Tous les types RAPID supportés par ce client
RAPID_TYPES: frozenset[str] = frozenset({
    "num",
    "bool",
    "string",
    "robtarget",
    "num[]",
    "bool[]",
    "string[]",
})

#: Types scalaires — délégués à serializers.py
_SCALAR_TYPES: frozenset[str] = frozenset({"num", "bool", "string", "robtarget"})

#: Types tableau — gérés dans ce module
_ARRAY_TYPES: frozenset[str] = frozenset({"num[]", "bool[]", "string[]"})

#: Type union pour toutes les valeurs RAPID supportées (PEP 604)
RapidValue = float | bool | str | list[float] | list[bool] | list[str] | RobTarget


# ---------------------------------------------------------------------------
# Construction des URLs
# ---------------------------------------------------------------------------


def build_symbol_path(var: str, module: str, task: str) -> str:
    """Construit le chemin RWS pour une variable RAPID.

    Correspond à la branche :
        /rw → /rapid → /symbol → /data → /RAPID/{task}/{module}/{var}

    Args:
        var: Nom de la variable RAPID (ex: "SPEED", "TARGET").
        module: Nom du module RAPID (ex: "MYMODULE").
        task: Nom de la tâche RAPID (ex: "T_ROB1").

    Returns:
        Chemin relatif sans slash initial.
        Exemple : "rw/rapid/symbol/data/RAPID/T_ROB1/MYMODULE/SPEED"
    """
    return f"{_SYMBOL_BASE}/{task}/{module}/{var}"


# ---------------------------------------------------------------------------
# Sérialisation des arrays (spécifique à ce module)
# ---------------------------------------------------------------------------


def _serialize_array(value: list[float] | list[bool] | list[str], rapid_type: str) -> str:
    """Sérialise un tableau Python en string RWS.

    Formats RWS :
        num[]    → "[1.0,2.0,3.0]"
        bool[]   → "[TRUE,FALSE,TRUE]"
        string[] → '["a","b","c"]'   (guillemets doubles, format JSON-compatible)

    Args:
        value: Liste Python à sérialiser.
        rapid_type: "num[]", "bool[]" ou "string[]".

    Raises:
        RWSValueError: Valeur incompatible avec le type déclaré.
    """
    if not isinstance(value, list):
        raise RWSValueError(
            f"Type '{rapid_type}' expects list, got {type(value).__name__}"
        )

    match rapid_type:
        case "num[]":
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value):
                raise RWSValueError(
                    "Type 'num[]' expects list[float | int], "
                    "got incompatible element(s)"
                )
            items = ",".join(str(float(v)) for v in value)
            return f"[{items}]"

        case "bool[]":
            if not all(isinstance(v, bool) for v in value):
                raise RWSValueError(
                    "Type 'bool[]' expects list[bool], got incompatible element(s)"
                )
            items = ",".join("TRUE" if v else "FALSE" for v in value)
            return f"[{items}]"

        case "string[]":
            if not all(isinstance(v, str) for v in value):
                raise RWSValueError(
                    "Type 'string[]' expects list[str], got incompatible element(s)"
                )
            # Format ABB : guillemets doubles autour de chaque élément
            # Ce format est un sous-ensemble valide de JSON
            items = ",".join(f'"{v}"' for v in value)
            return f"[{items}]"

        case _: # pragma: no cover
            raise RWSValueError(f"Not an array type: '{rapid_type}'")


# ---------------------------------------------------------------------------
# Désérialisation des arrays (spécifique à ce module)
# ---------------------------------------------------------------------------


def _deserialize_array(raw: str, rapid_type: str) -> list[float] | list[bool] | list[str]:
    """Désérialise une string RWS de type tableau vers une liste Python.

    Args:
        raw: Valeur brute issue du champ "lvalue" de la réponse RWS.
        rapid_type: "num[]", "bool[]" ou "string[]".

    Raises:
        RWSValueError: Format invalide ou éléments non parsables.
    """
    stripped = raw.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        raise RWSValueError(
            f"Invalid array format for '{rapid_type}' "
            f"(expected '[...]'): {raw!r}"
        )

    match rapid_type:
        case "num[]":
            inner = stripped[1:-1]
            if not inner:
                return []
            try:
                return [float(v.strip()) for v in inner.split(",")]
            except ValueError as exc:
                raise RWSValueError(
                    f"Non-numeric value in num[] {raw!r}: {exc}"
                ) from exc

        case "bool[]":
            inner = stripped[1:-1]
            if not inner:
                return []
            result: list[bool] = []
            for token in inner.split(","):
                t = token.strip().upper()
                if t not in ("TRUE", "FALSE"):
                    raise RWSValueError(
                        f"Invalid bool token {token!r} in bool[] {raw!r}"
                    )
                result.append(t == "TRUE")
            return result

        case "string[]":
            # Le format ABB string[] est du JSON valide → on délègue à json.loads
            try:
                parsed = _json.loads(stripped)
            except _json.JSONDecodeError as exc: # pragma: no cover
                raise RWSValueError(
                    f"JSON parse error in string[] {raw!r}: {exc}"
                ) from exc
            if not isinstance(parsed, list) or not all(isinstance(v, str) for v in parsed):
                raise RWSValueError(
                    f"Expected list[str] from string[], got mixed types in {raw!r}"
                )
            return parsed

        case _: # pragma: no cover
            raise RWSValueError(f"Not an array type: '{rapid_type}'")


# ---------------------------------------------------------------------------
# Dispatch sérialisation / désérialisation
# ---------------------------------------------------------------------------


def serialize_rapid_value(value: RapidValue, rapid_type: str) -> str:
    """Sérialise une valeur Python en string RWS pour le body PUT.

    Délègue aux serializers.py pour les scalaires,
    gère les arrays directement.

    Args:
        value: Valeur Python à sérialiser.
        rapid_type: Type RAPID cible (doit être dans RAPID_TYPES).

    Returns:
        String RWS prête à être envoyée dans le body PUT.

    Raises:
        RWSValueError: Type inconnu ou valeur incompatible.
    """
    if rapid_type not in RAPID_TYPES:
        raise RWSValueError(
            f"Unknown RAPID type '{rapid_type}'. "
            f"Supported: {sorted(RAPID_TYPES)}"
        )
    if rapid_type in _SCALAR_TYPES:
        # Délégation à serializers.py — gère num, bool, string, robtarget
        return python_to_rapid_value(value, rapid_type)  # type: ignore[arg-type]
    # Arrays
    return _serialize_array(value, rapid_type)  # type: ignore[arg-type]


def deserialize_rapid_value(raw: str, rapid_type: str) -> RapidValue:
    """Désérialise une string RWS en valeur Python.

    Délègue aux serializers.py pour les scalaires,
    gère les arrays directement.

    Args:
        raw: Valeur brute issue du champ "lvalue" de la réponse JSON RWS.
        rapid_type: Type RAPID déclaré.

    Returns:
        Valeur Python correspondante.

    Raises:
        RWSValueError: Type inconnu ou valeur non parsable.
    """
    if rapid_type not in RAPID_TYPES:
        raise RWSValueError(
            f"Unknown RAPID type '{rapid_type}'. "
            f"Supported: {sorted(RAPID_TYPES)}"
        )
    if rapid_type in _SCALAR_TYPES:
        return rapid_value_to_python(raw, rapid_type)
    return _deserialize_array(raw, rapid_type)


# ---------------------------------------------------------------------------
# Extraction du champ lvalue depuis la réponse JSON RWS
# ---------------------------------------------------------------------------


def extract_lvalue(response_json: dict) -> str:  # type: ignore[type-arg]
    """Extrait le champ 'lvalue' depuis la réponse JSON RWS.

    Structure attendue (GET /rw/rapid/symbol/data/...?json=1) :
        { "state": [ { "lvalue": "<valeur brute>" } ] }

    Args:
        response_json: Dictionnaire issu de response.json().

    Returns:
        Valeur brute sous forme de string.

    Raises:
        RWSValueError: Structure JSON inattendue.
    """
    try:
        return str(response_json["state"][0]["lvalue"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RWSValueError(
            f"Cannot extract 'state[0].lvalue' from RWS response: "
            f"{response_json!r}"
        ) from exc


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------


async def get_rapid_var(
    client: RWSClient,
    var: str,
    rapid_type: str,
    *,
    module: str,
    task: str = DEFAULT_TASK,
) -> RapidValue:
    """Lit une variable RAPID depuis le contrôleur ABB.

    Route : GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{var}?json=1

    La lecture ne nécessite PAS de mastership.

    Args:
        client: Instance RWSClient ouverte.
        var: Nom de la variable RAPID (ex: "SPEED", "FILENAMES").
        rapid_type: Type RAPID de la variable (ex: "num", "string[]").
        module: Module RAPID contenant la variable (paramètre nommé obligatoire).
        task: Tâche RAPID. Défaut : "T_ROB1".

    Returns:
        Valeur Python désérialisée :
        "num" → float | "bool" → bool | "string" → str
        "num[]" → list[float] | "bool[]" → list[bool] | "string[]" → list[str]
        "robtarget" → RobTarget

    Raises:
        RWSValueError: Type inconnu ou réponse mal formée.
        RWSNotFoundError: Variable inexistante dans le module/tâche.
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            speed = await get_rapid_var(client, "SPEED", "num", module="MYMOD")
            files = await get_rapid_var(client, "FILENAMES", "string[]", module="MYMOD")
    """
    path = build_symbol_path(var, module, task)
    logger.debug("GET RAPID var  path=%s  type=%s", path, rapid_type)

    response = await client.get(path, params={"json": "1"})

    try:
        data = response.json()
    except Exception as exc:
        raise RWSValueError(
            f"Failed to parse JSON response for '{var}': {exc}"
        ) from exc

    raw = extract_lvalue(data)
    value = deserialize_rapid_value(raw, rapid_type)

    logger.debug("GET '%s' = %r  (type=%s)", var, value, rapid_type)
    return value


async def set_rapid_var(
    client: RWSClient,
    var: str,
    value: RapidValue,
    rapid_type: str,
    *,
    module: str,
    task: str = DEFAULT_TASK,
) -> None:
    """Écrit une variable RAPID sur le contrôleur ABB.

    Route : PUT /rw/rapid/symbol/data/RAPID/{task}/{module}/{var}
            Body : value=<valeur>   (application/x-www-form-urlencoded)

    ⚠️  Doit être appelée dans un bloc Mastership — sans mastership,
    le contrôleur retourne HTTP 403.

    Args:
        client: Instance RWSClient ouverte.
        var: Nom de la variable RAPID.
        value: Valeur Python à écrire (doit correspondre au rapid_type).
        rapid_type: Type RAPID de la variable.
        module: Module RAPID (paramètre nommé obligatoire).
        task: Tâche RAPID. Défaut : "T_ROB1".

    Returns:
        None — RWS retourne 204 No Content sur succès.

    Raises:
        RWSValueError: Type inconnu ou valeur incompatible.
        RWSHTTPError: Erreur contrôleur (ex: 403 sans mastership).
        RWSNotFoundError: Variable inexistante.
        RWSConnectionError: Impossible de joindre le contrôleur.
        RWSTimeoutError: Timeout réseau.

    Example:
        ::

            async with Mastership(client):
                await set_rapid_var(client, "SPEED", 150.0, "num", module="MYMOD")
                await set_rapid_var(
                    client,
                    "FILENAMES",
                    ["part_A.prg", "part_B.prg"],
                    "string[]",
                    module="MYMOD",
                )
    """
    # Sérialisation avant toute requête réseau — lève RWSValueError si invalide
    serialized = serialize_rapid_value(value, rapid_type)
    path = build_symbol_path(var, module, task)

    logger.debug(
        "SET RAPID var  path=%s  type=%s  serialized=%r",
        path, rapid_type, serialized,
    )

    await client.put(path, data={"value": serialized})
    logger.debug("SET '%s' ← %r  (type=%s)", var, value, rapid_type)
