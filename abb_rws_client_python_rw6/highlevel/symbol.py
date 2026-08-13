# abb_rws_client_python_rw6/highlevel/symbol.py
"""High-level RAPID symbol introspection for ABB RWS RobotWare 6.

Author: Clement RACINET

Composed operations built exclusively from atomic ``rws/`` functions.
No HTTP calls are made directly in this module.

All functions are async and require an open ``RWSClient`` instance.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

import httpx

from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import get_logger
from abb_rws_client_python_rw6.rws.rapid.symbol import get_rapid_symbol_properties

logger = get_logger(__name__)

# ABB RWS XML span pattern, consistent with the parsing style already used
# in highlevel/variables.py and highlevel/execution.py.
_SPAN_RE_TEMPLATE = r'class=["\']{field}["\'][^>]*>([^<]*)<'

# FIXME (Clement RACINET):
# ABB doc ("Get RAPID symbol properties") only documents <span class="dim">
# for ndim=0 (empty). The separator used for ndim>=1 is NOT documented and
# has not been confirmed on real hardware. This parser is intentionally
# tolerant: it extracts every integer found in the "dim" span, regardless
# of separator (space, comma, or ABB's real format). MUST be confirmed on
# real hardware against an array symbol (e.g. trajTools{N}) before being
# relied upon for production sizing decisions. If ABB's real format breaks
# this extraction, fix _parse_dim accordingly — do not patch around it
# blindly.
_INT_RE = re.compile(r"-?\d+")


@dataclass(frozen=True)
class SymbolProperties:
    """Parsed RAPID symbol properties from ``GET /rw/rapid/symbol/properties``.

    Args:
        symbolurl: Symbol URL, e.g. ``"RAPID/T_ROB1/TRAJCENTER_CellConfig/trajTools"``.
        symtyp: Symbol type, e.g. ``"per"`` (persistent), ``"var"``, ``"con"``.
        dattyp: RAPID data type name, e.g. ``"trajCenterTool"``.
        ndim: Number of array dimensions. ``0`` means a scalar symbol.
        dim: Array dimension sizes, one entry per dimension. Empty when
            ``ndim == 0``.
        local: ``False`` for a global module persistent.
        readonly: ``True`` if the persistent is read-only.

    Example:
        ```python
        >>> props = SymbolProperties(
        ...     symbolurl="RAPID/T_ROB1/TRAJCENTER_CellConfig/trajTools",
        ...     symtyp="per",
        ...     dattyp="trajCenterTool",
        ...     ndim=1,
        ...     dim=(2,),
        ...     local=False,
        ...     readonly=False,
        ... )
        >>> props.dim[0]
        2
        ```
    """

    symbolurl: str
    symtyp: str
    dattyp: str
    ndim: int
    dim: tuple[int, ...]
    local: bool
    readonly: bool


def _extract_span(text: str, field: str) -> str | None:
    """Extract one ``<span class="{field}">...</span>`` value.

    Args:
        text: Raw XML/XHTML response body.
        field: ABB span class name, e.g. ``"ndim"``.

    Returns:
        The stripped span content, or ``None`` if not found.
    """
    match = re.search(_SPAN_RE_TEMPLATE.format(field=field), text)
    return match.group(1).strip() if match else None


def _parse_bool_span(text: str, field: str, *, default: bool) -> bool:
    """Parse an ABB ``{True|False}`` span value.

    Args:
        text: Raw XML/XHTML response body.
        field: ABB span class name.
        default: Value returned if the span is absent.

    Returns:
        Parsed boolean.
    """
    raw = _extract_span(text, field)
    if raw is None:
        return default
    return raw.strip().lower() == "true"


def _parse_dim(raw_dim: str) -> tuple[int, ...]:
    """Parse the ``dim`` span into a tuple of dimension sizes.

    ABB constraints:
        The exact separator used by ABB for ``ndim >= 1`` is not
        documented (confirmed absent from ABB's official page, which only
        shows the ``ndim=0`` / empty ``dim`` case). This parser extracts
        every integer token found, regardless of separator, and is NOT
        confirmed on real hardware for ``ndim >= 1``.

    Args:
        raw_dim: Raw ``dim`` span content, e.g. ``""`` or ``"2"`` or a
            multi-dimension form not yet observed on real hardware.

    Returns:
        Tuple of dimension sizes, in declared order. Empty tuple if
        ``raw_dim`` is empty or contains no integer.

    Example:
        ```python
        >>> _parse_dim("")
        ()
        >>> _parse_dim("2")
        (2,)
        ```
    """
    return tuple(int(token) for token in _INT_RE.findall(raw_dim))


def _parse_symbol_properties(response: httpx.Response, symbolurl: str) -> SymbolProperties:
    """Parse a ``GET /rw/rapid/symbol/properties/{symbolurl}`` response.

    Args:
        response: Raw HTTP response from ``get_rapid_symbol_properties``.
        symbolurl: Requested symbol URL, used for error messages and as a
            fallback if ``symburl`` cannot be parsed from the body.

    Returns:
        Parsed symbol properties.

    Raises:
        ValueError: If mandatory fields (``dattyp``, ``ndim``) cannot be
            extracted from the response body.

    Example:
        ```python
        resp = await get_rapid_symbol_properties(client, "RAPID/T_ROB1/M/trajTools")
        props = _parse_symbol_properties(resp, "RAPID/T_ROB1/M/trajTools")
        ```
    """
    text = response.text

    symtyp = _extract_span(text, "symtyp")
    dattyp = _extract_span(text, "dattyp")
    ndim_raw = _extract_span(text, "ndim")
    dim_raw = _extract_span(text, "dim") or ""

    if dattyp is None or ndim_raw is None:
        raise ValueError(
            "Cannot parse RAPID symbol properties from response "
            f"(symbolurl={symbolurl!r}): {text[:300]!r}"
        )

    return SymbolProperties(
        symbolurl=_extract_span(text, "symburl") or symbolurl,
        symtyp=symtyp or "",
        dattyp=dattyp,
        ndim=int(ndim_raw),
        dim=_parse_dim(dim_raw),
        local=_parse_bool_span(text, "local", default=True),
        readonly=_parse_bool_span(text, "ro", default=False),
    )


async def get_symbol_properties(
    client: RWSClient,
    *,
    symbolurl: str,
) -> SymbolProperties:
    """Read and parse the properties of a RAPID symbol.

    Wraps ``get_rapid_symbol_properties`` and parses the ABB XML response
    into a typed ``SymbolProperties``.

    Route (delegated): ``GET /rw/rapid/symbol/properties/{symbolurl}``

    ABB constraints:
        - Not supported in bootserver mode.
        - No mastership required for reads.

    Args:
        client: Open ``RWSClient`` instance.
        symbolurl: Full RAPID symbol path, e.g.
            ``"RAPID/T_ROB1/TRAJCENTER_CellConfig/trajTools"``.

    Returns:
        Parsed symbol properties, including array dimensions.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.
        ValueError: If the response body cannot be parsed.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            props = await get_symbol_properties(
                client,
                symbolurl="RAPID/T_ROB1/TRAJCENTER_CellConfig/trajTools",
            )
            print(props.ndim, props.dim)
        ```
    """
    response = await get_rapid_symbol_properties(client, symbolurl=symbolurl)
    return _parse_symbol_properties(response, symbolurl)


async def get_array_length(
    client: RWSClient,
    *,
    symbolurl: str,
    dimension: int = 0,
) -> int:
    """Read the size of one dimension of a RAPID array symbol.

    Convenience wrapper over ``get_symbol_properties`` for the common case
    of discovering a one-based array's usable upper bound at runtime
    (e.g. ``trajTools{N}`` where ``N`` is cell-dependent).

    Route (delegated): ``GET /rw/rapid/symbol/properties/{symbolurl}``

    ABB constraints:
        - The symbol must be declared as an array (``ndim >= 1``).
        - RAPID arrays are one-based; the returned length is the number of
          valid indexes ``1..length``.

    Args:
        client: Open ``RWSClient`` instance.
        symbolurl: Full RAPID symbol path of the array variable, e.g.
            ``"RAPID/T_ROB1/TRAJCENTER_CellConfig/trajTools"``.
        dimension: Zero-based index into ``SymbolProperties.dim`` for
            multi-dimensional arrays. Defaults to ``0`` (first dimension).

    Returns:
        Size of the requested dimension.

    Raises:
        RWSAuthenticationError: On HTTP 401.
        RWSNotFoundError: On HTTP 404.
        RWSHTTPError: On any other HTTP >= 400.
        ValueError: If the symbol is not an array (``ndim == 0``), or if
            ``dimension`` is out of range for the symbol's declared
            dimensions.

    Example:
        ```python
        async with RWSClient(host="192.168.125.1") as client:
            n = await get_array_length(
                client,
                symbolurl="RAPID/T_ROB1/TRAJCENTER_CellConfig/trajTools",
            )
            print("trajTools has", n, "entries")
        ```
    """
    props = await get_symbol_properties(client, symbolurl=symbolurl)

    if props.ndim == 0:
        raise ValueError(f"Symbol {symbolurl!r} is not an array (ndim=0)")

    if dimension < 0 or dimension >= len(props.dim):
        raise ValueError(
            f"dimension={dimension} out of range for symbol {symbolurl!r} with dim={props.dim!r}"
        )

    length = props.dim[dimension]
    logger.debug("Array %s dimension %d length = %d", symbolurl, dimension, length)
    return length
