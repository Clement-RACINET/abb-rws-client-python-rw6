# abb_rws_client_python_rw6/highlevel/symbol.py
"""High-level RAPID symbol introspection for ABB RWS RobotWare 6.

Author: Clement RACINET

Provides typed helper functions around ABB RWS RAPID symbol introspection.

This module does not perform raw HTTP calls directly. It delegates transport
to atomic functions from ``abb_rws_client_python_rw6.rws`` and only parses
their ABB XML/XHTML responses into Python data structures.

Main features:
    - read RAPID symbol properties;
    - extract symbol type and RAPID data type;
    - detect scalar vs array symbols;
    - read RAPID array dimension lengths.

ABB constraints:
    - Symbol properties are read through
      ``GET /rw/rapid/symbol/properties/{symbolurl}``.
    - Reads do not require mastership.
    - The endpoint is not supported in bootserver mode.
    - RAPID arrays are one-based on the controller side, but Python dimension
      selection in this module is zero-based.

All public functions are asynchronous and require an open ``RWSClient``.
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

# ABB documentation for "Get RAPID symbol properties" documents an empty
# ABB returns array dimensions in the "dim" span of
# GET /rw/rapid/symbol/properties/{symbolurl}. The scalar case returns an
# empty value. The 1D array case was confirmed on real RW6 hardware with
# PERS num Array1D{4}, returned as dim=(4,). The parser remains tolerant and
# extracts integer tokens to support possible multi-dimensional formats.
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
    """Extract one ABB XML/XHTML ``<span class="{field}">`` value.

    Route: N/A — local ABB response parser.

    ABB constraints: ABB RWS symbol-property responses encode fields as
        ``<span>`` elements whose CSS class carries the field name.

    Args:
        text: Raw XML/XHTML response body.
        field: ABB span class name, e.g. ``"ndim"``.

    Returns:
        The stripped span content, or ``None`` if not found.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> _extract_span('<span class="ndim">1</span>', "ndim")
        '1'
        ```
    """
    match = re.search(_SPAN_RE_TEMPLATE.format(field=field), text)
    return match.group(1).strip() if match else None


def _parse_bool_span(text: str, field: str, *, default: bool) -> bool:
    """Parse an ABB XML/XHTML boolean span value.

    Route: N/A — local ABB response parser.

    ABB constraints: ABB symbol-property boolean fields are expected as text
        values such as ``"true"`` or ``"false"`` inside a ``<span>``.

    Args:
        text: Raw XML/XHTML response body.
        field: ABB span class name.
        default: Value returned if the span is absent.

    Returns:
        Parsed boolean value. Missing fields return ``default``.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> _parse_bool_span('<span class="ro">false</span>', "ro", default=True)
        False
        ```
    """
    raw = _extract_span(text, field)
    if raw is None:
        return default
    return raw.strip().lower() == "true"


def _parse_dim(raw_dim: str) -> tuple[int, ...]:
    """Parse an ABB ``dim`` span into array dimension sizes.

    Route: N/A — local ABB response parser.

    ABB constraints: ABB returns an empty ``dim`` span for scalar symbols
        where ``ndim=0``. A one-dimensional RAPID array was confirmed on real
        RW6 hardware as one integer dimension value. The parser extracts
        integer tokens defensively to support possible multi-dimensional
        formats.

    Args:
        raw_dim: Raw ``dim`` span content, e.g. ``""``, ``"2"``, ``"2 3"``,
            ``"2,3"``, or another controller-specific multi-dimension form.

    Returns:
        Tuple of dimension sizes in declared order. Empty tuple if
        ``raw_dim`` is empty or contains no integer.

    Raises:
        No exception is raised by this helper.

    Example:
        ```python
        >>> _parse_dim("")
        ()
        >>> _parse_dim("2")
        (2,)
        >>> _parse_dim("2,3")
        (2, 3)
        ```
    """
    return tuple(int(token) for token in _INT_RE.findall(raw_dim))


def _parse_symbol_properties(response: httpx.Response, symbolurl: str) -> SymbolProperties:
    """Parse a RAPID symbol-property response into ``SymbolProperties``.

    Route: Parses response from
        ``GET /rw/rapid/symbol/properties/{symbolurl}``.

    ABB constraints:
        - ``dattyp`` and ``ndim`` are mandatory for this parser.
        - ``ndim=0`` means scalar symbol.
        - ``ndim>=1`` means array symbol.
        - ``dim`` should contain one size per declared dimension.

    Args:
        response: Raw HTTP response from ``get_rapid_symbol_properties``.
        symbolurl: Requested symbol URL, used for error messages and as a
            fallback if ``symburl`` cannot be parsed from the body.

    Returns:
        Parsed symbol properties.

    Raises:
        ValueError: If mandatory fields cannot be extracted, if ``ndim`` is
            not an integer, or if the parsed dimensions are inconsistent with
            ``ndim``.

    Example:
        ```python
        resp = await get_rapid_symbol_properties(
            client,
            symbolurl="RAPID/T_ROB1/M/trajTools",
        )
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

    try:
        ndim = int(ndim_raw)
    except ValueError as exc:
        raise ValueError(f"Cannot parse ndim={ndim_raw!r} for symbolurl={symbolurl!r}") from exc

    dim = _parse_dim(dim_raw)

    if ndim == 0 and dim:
        raise ValueError(
            f"Inconsistent scalar symbol properties for {symbolurl!r}: ndim=0 but dim={dim!r}"
        )

    if ndim > 0 and len(dim) != ndim:
        raise ValueError(
            f"Inconsistent array symbol properties for {symbolurl!r}: ndim={ndim}, dim={dim!r}"
        )

    return SymbolProperties(
        symbolurl=_extract_span(text, "symburl") or symbolurl,
        symtyp=symtyp or "",
        dattyp=dattyp,
        ndim=ndim,
        dim=dim,
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
