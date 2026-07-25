#!/usr/bin/env python3
# utils/generator/main.py
"""
Source code generator for abb_rws_client/rws/.

Author: Clement RACINET

Reads  : utils/scraping/abb_rws_api_full.json
Writes : abb_rws_client/rws/**/*.py
         tests/rws/**/*.py

This script is an internal development tool.
It is NOT part of the published library (pyproject.toml → packages = ["abb_rws_client_python_rw6"]).

Usage:
    python utils/generator/main.py [--dry-run] [--only <module_path>]

Options:
    --dry-run          Print what would be generated without writing any files.
    --only <path>      Only generate the specified module (e.g. rapid/execution).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import textwrap

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
API_JSON = REPO_ROOT / "utils" / "scraping" / "abb_rws_api_full.json"
RWS_OUT = REPO_ROOT / "abb_rws_client_python_rw6" / "rws"
TESTS_OUT = REPO_ROOT / "tests" / "rws"

# Maximum line length (matches ruff line-length = 100, with 3 chars margin)
_MAX_LINE = 97

# ---------------------------------------------------------------------------
# Breadcrumb → Python module path mapping  (inchangé)
# ---------------------------------------------------------------------------

_ROUTING_TABLE: dict[str, str | dict] = {
    "Root Resource": "root",
    "Subscription Service": "subscription",
    "User Service": {
        "__default__": "users/misc",
        "Get User Resources": "users/users",
        "Get User Actions": "users/users",
        "Register the user": "users/users",
        "Impersonate a user": "users/users",
        "Login as Local User": "users/users",
        "Operations on Users grants": "users/grants",
        "Get User grants": "users/grants",
        "Operations on RMMP": "users/rmmp",
        "Get RMMP state": "users/rmmp",
        "Get RMMP Actions": "users/rmmp",
        "Request RMMP": "users/rmmp",
        "Grant or deny an RMMP request": "users/rmmp",
        "Cancel held or requested RMMP": "users/rmmp",
        "Subscribe on RMMP Request event": "users/rmmp",
        "Poll for RMMP grant status": "users/rmmp",
        "Operations on Remote User": "users/remote",
        "Get remote user actions": "users/remote",
        "Remote User Logon Request": "users/remote",
        "Remote User Logout Request": "users/remote",
        "Subscribe on remote user state": "users/remote",
    },
    "Controller Service": {
        "__default__": "ctrl/ctrl",
        "Get Controller Resources": "ctrl/ctrl",
        "Get Controller Actions": "ctrl/ctrl",
        "Get Controller environment variable": "ctrl/ctrl",
        "Restart or Shutdown controller": "ctrl/ctrl",
        "Set Controller language": "ctrl/ctrl",
        "Operations on Clock Resource": "ctrl/clock",
        "Get Clock Resource": "ctrl/clock",
        "Get Clock Actions": "ctrl/clock",
        "Set Controller Clock": "ctrl/clock",
        "Operations on Identity Resource": "ctrl/identity",
        "Get Identity Resource": "ctrl/identity",
        "Operations on Network Resource": "ctrl/network",
        "Get Network Resource": "ctrl/network",
        "Get Network Actions": "ctrl/network",
        "Set Network Resource": "ctrl/network",
        "Operations on Controller Options": "ctrl/options",
        "Get Controller Options": "ctrl/options",
        "Operations on Backup Resource": "ctrl/backup",
        "Get Backup Resource": "ctrl/backup",
        "Get Backup Actions": "ctrl/backup",
        "Create Backup": "ctrl/backup",
        "Restore Backup": "ctrl/backup",
    },
    "File Service": "fileservice",
    "RobotWare Services": {
        "__default__": "rw/misc",
        "CFG Service": "cfg",
        "DIPC service": "dipc",
        "Elog service": "elog",
        "IO Service": {
            "__default__": "iosystem/iosystem",
            "Operations on IO Signals": "iosystem/signals",
            "Get IO Signals": "iosystem/signals",
            "Get IO Signal": "iosystem/signals",
            "Get IO Signal Actions": "iosystem/signals",
            "Set IO Signal": "iosystem/signals",
            "Subscribe on IO Signal": "iosystem/signals",
            "Operations on IO Networks": "iosystem/networks",
            "Get IO Networks": "iosystem/networks",
            "Get IO Network": "iosystem/networks",
            "Operations on IO Devices": "iosystem/devices",
            "Get IO Devices": "iosystem/devices",
            "Get IO Device": "iosystem/devices",
            "Operations on IO Profinet Device": "iosystem/profinet",
        },
        "Mastership service": "mastership",
        "Panel service": "panel",
        "RAPID Service": {
            "__default__": "rapid/rapid",
            "Operations on RAPID execution": "rapid/execution",
            "Operations on RAPID modules": "rapid/modules",
            "Operations on RAPID symbols properties": "rapid/symbols",
            "Operations on RAPID symbol": "rapid/symbol",
            "Operations on RAPID tasks": "rapid/tasks",
            "Operations on RAPID UI instructions": "rapid/uiinstr",
            "Operations on Rapid taskpanel": "rapid/taskpanel",
            "Operations on Rapid AliasIO": "rapid/aliasio",
        },
        "System service": "system",
        "RobotWare return codes service": "retcode",
        "Devices service": "devices",
        "Motion System": "motionsystem",
        "Integrated Vision (IV) Service": "vision",
    },
}

# ---------------------------------------------------------------------------
# Known ABB documentation typos
# ---------------------------------------------------------------------------
#
# ABB's official RWS doc for the Subscription Service contains a typo:
# "/subscripion/{...}" instead of "/subscription/{...}" (missing "t").
#
# Confirmed on a real RW6 controller (2026-07-25, C. RACINET):
#   DELETE /subscription/{group_id}  → 204, subscription actually removed.
#   The doc-literal "/subscripion/"  → would 404 (unroutable path on ABB side).
#
# The scraped JSON is left untouched (verbatim capture of ABB's doc, kept
# for diffing against future ABB doc revisions). The fix is applied here,
# at generation time, so it survives every regeneration.
#
# Also normalizes the inconsistent path param "{group-d}" → "{group-id}"
# on the same buggy endpoint, so the generated Python parameter name is
# "group_id" everywhere instead of the ABB-doc-typo "group_d".
_URL_TYPO_FIXES: dict[str, str] = {
    "/subscripion/{group-id}": "/subscription/{group-id}",
    "/subscripion/{group-id}/{resource-uri}": "/subscription/{group-id}/{resource-uri}",
    "/subscripion/{group-d}/{resource-uri}": "/subscription/{group-id}/{resource-uri}",
}


def _apply_known_typo_fixes(endpoints: list[dict]) -> None:
    """Patch known ABB documentation URL typos in-place.

    Tracks which entries of ``_URL_TYPO_FIXES`` actually matched an URL
    in the scraped JSON. Any entry that matched zero endpoints is
    reported as a stale patch: either ABB fixed their documentation, or
    the JSON structure changed upstream. Stale entries must be removed
    from ``_URL_TYPO_FIXES`` — leaving them in place is silent dead code
    that hides a future regression if the typo ever comes back.

    Args:
        endpoints: Raw endpoint list as loaded from the scraped JSON.
            Mutated in place — the source JSON file on disk is never
            modified.
    """
    matched: set[str] = set()

    for ep in endpoints:
        url = ep.get("url", "")
        if url in _URL_TYPO_FIXES:
            fixed = _URL_TYPO_FIXES[url]
            matched.add(url)
            print(f"[FIX]  Known ABB doc typo corrected: {url!r} -> {fixed!r}")
            ep["url"] = fixed

    stale = set(_URL_TYPO_FIXES) - matched
    for stale_url in sorted(stale):
        print(
            f"[WARN] Typo patch for {stale_url!r} matched NOTHING in the scraped JSON.\n"
            f"       Either ABB fixed their documentation, or the JSON structure\n"
            f"       changed upstream. This patch entry is now dead code.\n"
            f"       ACTION REQUIRED: remove it from _URL_TYPO_FIXES in "
            f"utils/generator/main.py."
        )

def resolve_module_path(breadcrumb: list[str]) -> str | None:
    """Resolve the Python module path (relative to rws/) from an ABB breadcrumb.

    Walks ``_ROUTING_TABLE`` level by level.
    Returns ``None`` for navigation nodes that have no endpoint.

    Args:
        breadcrumb: List of strings extracted from the ABB JSON.

    Returns:
        Relative path (e.g. ``"rapid/execution"``, ``"users/rmmp"``)
        or ``None`` if the node is a navigation-only page.
    """
    if not breadcrumb or len(breadcrumb) < 2:
        return None

    level0 = breadcrumb[0]
    node: str | dict | None = _ROUTING_TABLE.get(level0)

    if node is None:
        return _slugify(level0)
    if isinstance(node, str):
        return node

    level1 = breadcrumb[1]
    sub: str | dict | None = node.get(level1)  # type: ignore[union-attr]

    if sub is None:
        default: str = node.get("__default__", _slugify(level0))  # type: ignore[assignment]
        return default
    if isinstance(sub, str):
        return sub

    if len(breadcrumb) < 3:
        default2: str = sub.get("__default__", f"{_slugify(level0)}/{_slugify(level1)}")  # type: ignore[assignment]
        return default2

    level2 = breadcrumb[2]
    subsub: str | None = sub.get(level2)  # type: ignore[union-attr]

    if subsub is None:
        default3: str = sub.get("__default__", f"{_slugify(level0)}/{_slugify(level1)}/misc")  # type: ignore[assignment]
        return default3

    return subsub


def _slugify(text: str) -> str:
    """Convert an ABB name to a valid Python slug (snake_case).

    Args:
        text: Raw text (e.g. ``"IO Service"``).

    Returns:
        Slug (e.g. ``"io_service"``).
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s_]", "", slug)
    slug = re.sub(r"\s+", "_", slug).strip("_")
    return slug


# ---------------------------------------------------------------------------
# Grouping endpoints by module
# ---------------------------------------------------------------------------


def group_by_module(endpoints: list[dict]) -> dict[str, list[dict]]:
    """Group endpoints by Python module path.

    Filters out nodes without a URL or HTTP method (navigation pages).

    Args:
        endpoints: Raw list from the ABB JSON.

    Returns:
        Dictionary ``{module_path: [endpoint, ...]}``.
    """
    result: dict[str, list[dict]] = {}
    skipped = 0

    for ep in endpoints:
        url = ep.get("url", "").strip()
        method = ep.get("method", "").strip()
        breadcrumb = ep.get("breadcrumb", [])

        if not url or not method:
            skipped += 1
            continue

        module_path = resolve_module_path(breadcrumb)
        if module_path is None:
            skipped += 1
            continue

        result.setdefault(module_path, []).append(ep)

    total = sum(len(v) for v in result.values())
    print(f"[INFO] {total} endpoints → {len(result)} modules ({skipped} navigation nodes skipped)")
    return result


# ---------------------------------------------------------------------------
# ABB parameter name sanitisation
# ---------------------------------------------------------------------------


def _sanitize_param_name(raw: str, max_len: int = 38) -> str:  # ← 40 → 38
    """Convert an ABB parameter name to a valid Python identifier.

    Truncates to ``max_len`` characters to prevent excessively long
    parameter names from generating ``E501`` violations in function
    signatures and generated dict comprehensions.

    The default of 38 ensures that even in the most deeply indented
    context (16 spaces for dict items inside ``_render_kwarg``), the
    generated line stays within the 100-character limit:
    ``16 + 1 + 38 + 1 + 2 + 38 + 1 = 97 ≤ 100``.

    Args:
        raw: Raw ABB name (e.g. ``"domain-name"``).
        max_len: Maximum length of the returned identifier. Default: 38.

    Returns:
        Valid Python identifier, at most ``max_len`` characters long.
    """
    name = re.sub(r"[^a-z0-9_]", "_", raw.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name[:max_len]


def extract_path_params(url: str) -> list[str]:
    """Extract and sanitise ``{param}`` path parameters from an ABB URL.

    Args:
        url: ABB URL (e.g. ``/rw/mastership/{domain-name}``).

    Returns:
        Sanitised names (e.g. ``["domain_name"]``).
    """
    return [_sanitize_param_name(p) for p in re.findall(r"\{([^}]+)\}", url)]


def build_url_expr(url: str) -> str:
    """Build the Python expression for a URL (string literal or f-string).

    Args:
        url: Raw ABB URL (e.g. ``"/rw/mastership/{domain-name}"``).

    Returns:
        Python expression (e.g. ``'f"/rw/mastership/{domain_name}"'``).
    """
    raw_params = re.findall(r"\{([^}]+)\}", url)
    if not raw_params:
        return f'"{url}"'

    py_url = url
    for raw in raw_params:
        py_url = py_url.replace(f"{{{raw}}}", f"{{{_sanitize_param_name(raw)}}}")

    return f'f"{py_url}"'


# ---------------------------------------------------------------------------
# ABB parameter parsing
# ---------------------------------------------------------------------------


def parse_success_code(success_raw: str) -> int:
    """Extract the first HTTP success code from an ABB description string.

    Args:
        success_raw: Raw string (e.g. ``"HTTP_OK(200), see HTTP Status codes"``).

    Returns:
        Integer HTTP code. Default: 200.
    """
    match = re.search(r"\b(200|201|202|204)\b", success_raw or "")
    return int(match.group(1)) if match else 200


def parse_query_params(url_params_raw: str) -> list[tuple[str, bool]]:
    """Extract query parameters from the ABB ``url_params`` field.

    Args:
        url_params_raw: Raw content of the ``url_params`` field.

    Returns:
        List of ``(python_name, is_required)`` tuples.
    """
    if not url_params_raw or url_params_raw.strip().lower() in ("none", ""):
        return []

    params: list[tuple[str, bool]] = []
    seen: set[str] = set()

    for line in url_params_raw.splitlines():
        line = line.strip()
        if "=" not in line:
            continue
        if line.startswith(("See", "*", "In the", "The ", "Note", "curl")):
            continue

        raw_name = line.split("=", 1)[0].strip().strip("*[]").strip()
        py_name = _sanitize_param_name(raw_name)  # ← max_len=40 appliqué

        if not py_name or py_name in seen:
            continue
        seen.add(py_name)

        is_required = bool(re.search(r"\bRequired\b", line, re.IGNORECASE))
        params.append((py_name, is_required))

    return params[:6]


def parse_body_params(data_params_raw: str) -> list[tuple[str, bool]]:
    """Extract body parameters from the ABB ``data_params`` field.

    Args:
        data_params_raw: Raw content of the ``data_params`` field.

    Returns:
        List of ``(python_name, is_required)`` tuples.
    """
    if not data_params_raw or data_params_raw.strip().lower() in ("none", "none*", ""):
        return []

    params: list[tuple[str, bool]] = []
    seen: set[str] = set()

    for line in data_params_raw.splitlines():
        line = line.strip()
        if "=" not in line:
            continue
        if line.startswith(("See", "curl", "Note", "The ", "In the")):
            continue

        raw_name = line.split("=", 1)[0].strip().strip("*[]'\"").strip()
        py_name = _sanitize_param_name(raw_name)  # ← max_len=40 appliqué

        if not py_name or py_name in seen:
            continue
        seen.add(py_name)

        is_required = bool(re.search(r"\bRequired\b", line, re.IGNORECASE))
        params.append((py_name, is_required))

    return params[:10]


# ---------------------------------------------------------------------------
# Function naming  ← CORRIGÉ : déduplication F811
# ---------------------------------------------------------------------------

_VERB_PREFIXES = frozenset(
    {
        "get",
        "set",
        "post",
        "put",
        "delete",
        "create",
        "update",
        "start",
        "stop",
        "request",
        "release",
        "subscribe",
        "unsubscribe",
        "load",
        "save",
        "reset",
        "restart",
        "validate",
        "register",
        "login",
        "logout",
        "grant",
        "cancel",
        "poll",
        "add",
        "remove",
        "impersonate",
    }
)


def endpoint_to_func_name(ep: dict, _counter: dict[str, int] | None = None) -> str:
    """Convert an endpoint to a unique snake_case Python function name.

    Uses the ABB ``title`` field. Prefixes with the HTTP method if the
    title does not already start with a recognised verb.
    Appends a numeric suffix (``_2``, ``_3``...) when the same base name
    is generated for multiple endpoints in the same module, preventing
    ``F811`` redefinition errors.

    Args:
        ep: Endpoint dictionary extracted from the ABB JSON.
        _counter: Mutable name-counter shared across a module's endpoints.
            Pass a fresh ``{}`` at the start of each module to enable
            per-module deduplication. If ``None``, no deduplication is
            applied (legacy behaviour, kept for backward compatibility).

    Returns:
        Valid, unique Python function name (e.g. ``"get_execution_state_2"``).
    """
    title: str = ep.get("title", "unknown")
    method: str = ep.get("method", "get").lower()

    name = title.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    words = [w for w in name.split() if w and len(w) > 1]
    words = words[:7]

    func = "_".join(words)
    func = re.sub(r"_+", "_", func).strip("_")

    first_word = words[0] if words else ""
    if first_word not in _VERB_PREFIXES:
        func = f"{method}_{func}"

    # ── Déduplication par suffixe numérique ───────────────────────────────
    if _counter is not None:
        count = _counter.get(func, 0) + 1
        _counter[func] = count
        if count > 1:
            func = f"{func}_{count}"

    return func


# ---------------------------------------------------------------------------
# Docstring line wrapping  ← NOUVEAU : corrige E501
# ---------------------------------------------------------------------------


def _wrap_doc(text: str, indent: str = "    ", max_width: int = _MAX_LINE) -> list[str]:
    """Wrap a docstring text block to fit within ``max_width`` total characters.

    Args:
        text: Raw text to wrap (without leading indent).
        indent: Indentation prefix applied to every output line.
        max_width: Maximum total line width (indent + text).

    Returns:
        List of indented, wrapped lines. Never empty: returns
        ``[indent + text]`` unchanged if wrapping is impossible.
    """
    available = max_width - len(indent)
    if available <= 0:
        return [f"{indent}{text}"]
    wrapped = textwrap.wrap(
        text,
        width=available,
        break_long_words=True,
        break_on_hyphens=False,
        subsequent_indent="    ",  # continuation indent inside the docstring block
    )
    return [f"{indent}{line}" for line in wrapped] if wrapped else [f"{indent}{text}"]


# ---------------------------------------------------------------------------
# Helpers de rendu HTTP
# ---------------------------------------------------------------------------


def _split_dict_items(items_str: str) -> list[str]:
    """Split a comma-separated dict items string respecting nesting depth.

    Args:
        items_str: Raw items string (e.g. ``'"a": x, "b": y'``).

    Returns:
        List of individual item strings (e.g. ``['"a": x', '"b": y']``).
    """
    items: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in items_str:
        if ch in ("{", "[", "("):
            depth += 1
            current.append(ch)
        elif ch in ("}", "]", ")"):
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
        else:
            current.append(ch)
    item = "".join(current).strip()
    if item:
        items.append(item)
    return items


def _render_kwarg(kwarg: str, indent: str = "        ") -> list[str]:
    """Render a single httpx keyword argument, splitting long dict literals.

    When a ``params={...}`` or ``data={...}`` comprehension would produce a
    line longer than ``_MAX_LINE`` characters, the source dict items are
    each placed on their own line inside the comprehension.

    Args:
        kwarg: Full kwarg string
            (e.g. ``'params={k: v for k, v in {"a": a}.items() if v is not None}'``).
        indent: Indentation prefix for the output lines.

    Returns:
        One or more lines rendering the kwarg, always ending with a comma.
    """
    full_line = f"{indent}{kwarg},"
    if len(full_line) <= _MAX_LINE:
        return [full_line]

    # Pattern: params={k: v for k, v in {ITEMS}.items() if v is not None}
    match = re.match(
        r"^(params|data)=\{k: v for k, v in \{(.+)\}\.items\(\) if v is not None\}$",
        kwarg,
        re.DOTALL,
    )
    if not match:
        # Fixed params dict (no comprehension) — split on comma+space boundary
        # e.g. params={"action": "show", "type": "selected"}
        kv_match = re.match(r"^(params|data)=\{(.+)\}$", kwarg, re.DOTALL)
        if kv_match:
            kw_name = kv_match.group(1)
            raw_items = _split_dict_items(kv_match.group(2))
            inner = indent + "    "
            result = [f"{indent}{kw_name}={{"]
            for i, item in enumerate(raw_items):
                comma = "," if i < len(raw_items) - 1 else ""
                result.append(f"{inner}{item}{comma}")
            result.append(f"{indent}}},")
            return result
        # Unrecognised pattern — keep as-is, accept the E501
        return [full_line]

    kw_name = match.group(1)  # "params" or "data"
    items_str = match.group(2)  # '"key1": var1, "key2": var2, ...'
    raw_items = _split_dict_items(items_str)

    inner = indent + "    "
    dict_inner = inner + "    "

    result = [f"{indent}{kw_name}={{"]
    result.append(f"{inner}k: v")
    result.append(f"{inner}for k, v in {{")
    for i, item in enumerate(raw_items):
        comma = "," if i < len(raw_items) - 1 else ""
        result.append(f"{dict_inner}{item}{comma}")
    result.append(f"{inner}}}.items()")
    result.append(f"{inner}if v is not None")
    result.append(f"{indent}}},")
    return result


def _render_http_call(
    method_lower: str,
    url_expr: str,
    httpx_kwargs: list[str],
) -> list[str]:
    """Render the ``return await client.X(...)`` statement as multiple lines.

    Always uses the multi-line form. Each kwarg is further split by
    ``_render_kwarg`` when it would exceed ``_MAX_LINE`` characters.

    Args:
        method_lower: HTTP method in lowercase (e.g. ``"get"``).
        url_expr: Python URL expression (e.g. ``'"/rw/cfg"'``).
        httpx_kwargs: List of keyword argument strings.

    Returns:
        List of Python source lines.
    """
    if not httpx_kwargs:
        return [f"    return await client.{method_lower}({url_expr})"]

    lines = [f"    return await client.{method_lower}("]
    lines.append(f"        {url_expr},")
    for kwarg in httpx_kwargs:
        lines.extend(_render_kwarg(kwarg))
    lines.append("    )")
    return lines


def _render_path_assert(expected_path: str) -> list[str]:
    """Render the ``url.path`` assertion, using a variable if too long.

    Args:
        expected_path: The expected URL path string.

    Returns:
        One line (direct assert) or two lines (variable + assert).
    """
    direct = f'    assert transport.last_request.url.path == "{expected_path}"'
    if len(direct) <= _MAX_LINE:
        return [direct]
    return [
        f'    expected_path = "{expected_path}"',
        "    assert transport.last_request.url.path == expected_path",
    ]


def _render_call_line(call_str: str) -> list[str]:
    """Render ``resp = await func(...)`` splitting args if the line is too long.

    Args:
        call_str: The full call expression (e.g. ``'await f(client, "x")'``).

    Returns:
        One or more lines.
    """
    line = f"    resp = {call_str}"
    if len(line) <= _MAX_LINE:
        return [line]

    paren_idx = call_str.index("(")
    func_part = call_str[: paren_idx + 1]
    args_str = call_str[paren_idx + 1 : -1]
    args = _split_dict_items(args_str)  # réutilise le splitter depth-aware

    result = [f"    resp = {func_part}"]
    for i, arg in enumerate(args):
        comma = "," if i < len(args) - 1 else ""
        result.append(f"        {arg}{comma}")
    result.append("    )")
    return result


# ---------------------------------------------------------------------------
# rws/ module generation
# ---------------------------------------------------------------------------


def _compute_func_names(endpoints: list[dict]) -> list[str]:
    """Pre-compute unique function names for a list of endpoints.

    Uses a shared counter so that both ``render_module`` and
    ``render_tests`` produce identical names for the same endpoints.

    Args:
        endpoints: Ordered list of endpoint dicts for one module.

    Returns:
        List of unique function names, same length and order as
        ``endpoints``.
    """
    counter: dict[str, int] = {}
    return [endpoint_to_func_name(ep, _counter=counter) for ep in endpoints]


def render_module(module_path: str, endpoints: list[dict]) -> str:
    """Generate the full content of an rws/ module file.

    Args:
        module_path: Relative path (e.g. ``"rapid/execution"``).
        endpoints: List of endpoints for this module.

    Returns:
        Python file content as a string.
    """
    first_bc = endpoints[0].get("breadcrumb", []) if endpoints else []
    title = " → ".join(first_bc[:3]) if first_bc else module_path
    title = title.replace("\\", "/")

    # Tronquer le titre pour que "RWS module: {title}" ne dépasse pas _MAX_LINE
    prefix = "RWS module: "
    max_title_len = _MAX_LINE - len(prefix)
    if len(title) > max_title_len:
        title = title[: max_title_len - 3] + "..."

    func_names = _compute_func_names(endpoints)

    lines: list[str] = [
        "# This file is AUTO-GENERATED by utils/generator/main.py",
        "# DO NOT EDIT MANUALLY — run the generator to regenerate.",
        "#  Generator author: Clement RACINET",
        '"""',
        f"{prefix}{title}",
        "",
        "1:1 mirror of the ABB RobotWare 6 REST API.",
        "Each function maps to exactly one HTTP endpoint.",
        "No composed logic — see highlevel/ for wrappers.",
        '"""',
        "from __future__ import annotations",
        "",
        "import httpx",
        "",
        "from abb_rws_client_python_rw6.core.client import RWSClient",
        "",
        "",
    ]

    for ep, func_name in zip(
        endpoints,
        func_names,
        strict=False,
    ):
        lines.extend(render_function(ep, func_name=func_name))
        lines.append("")

    return "\n".join(lines)


def render_function(ep: dict, *, func_name: str | None = None) -> list[str]:
    """Generate the async function code for an ABB endpoint.

    Note:
        The ``notes`` field from the ABB JSON may contain backslashes.
        These are replaced by forward slashes before being injected into
        docstrings to prevent ``SyntaxError``.

        Required parameters are always placed before optional parameters.

        All docstring lines are wrapped to ``_MAX_LINE`` characters to
        satisfy ``E501``.

        All POST and PUT requests include ``data={}`` at minimum, even
        when the ABB endpoint declares no body parameters. This ensures
        httpx always sends ``Content-Type: application/x-www-form-urlencoded``,
        which ABB RW6 requires on every POST/PUT — returning HTTP 415
        otherwise.

    Args:
        ep: Endpoint dictionary extracted from the ABB JSON.
        func_name: Pre-computed unique function name. If ``None``,
            ``endpoint_to_func_name`` is called without deduplication
            (backward-compatible fallback).

    Returns:
        List of Python lines (no trailing newline).
    """
    if func_name is None:
        func_name = endpoint_to_func_name(ep)

    url: str = ep.get("url", "")
    method: str = ep.get("method", "GET").upper()
    title: str = ep.get("title", "")
    notes: str = (ep.get("notes") or "").strip()
    success_raw: str = ep.get("success_response") or ""
    error_raw: str = ep.get("error_response") or ""

    path_params = extract_path_params(url)
    query_params = parse_query_params(ep.get("url_params") or "")
    body_params = parse_body_params(ep.get("data_params") or "")

    # ── Signature ─────────────────────────────────────────────────────────
    sig_parts: list[str] = ["client: RWSClient"]
    sig_parts += [f"{p}: str" for p in path_params]

    _url_qs_keys = {
        pair.split("=")[0].strip()
        for pair in (url.split("?")[1] if "?" in url else "").split("&")
        if "=" in pair
    }
    query_required = [f"{n}: str" for n, req in query_params if req and n not in _url_qs_keys]
    query_optional = [
        f"{n}: str | None = None" for n, req in query_params if not req and n not in _url_qs_keys
    ]
    body_required = [f"{n}: str" for n, req in body_params if req]
    body_optional = [f"{n}: str | None = None" for n, req in body_params if not req]
    sig_parts += query_required + body_required + query_optional + body_optional

    # ── URL split ─────────────────────────────────────────────────────────
    url_path = url.split("?")[0]
    url_qs = url.split("?")[1] if "?" in url else ""
    url_expr = build_url_expr(url_path)

    # ── httpx kwargs ──────────────────────────────────────────────────────
    httpx_kwargs: list[str] = []

    fixed_qs_pairs: list[tuple[str, str]] = []
    if url_qs:
        for pair in url_qs.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    fixed_qs_pairs.append((k, v))

    fixed_qs_keys_func: set[str] = {k for k, _ in fixed_qs_pairs}
    dynamic_query_params = [(n, req) for n, req in query_params if n not in fixed_qs_keys_func]

    if fixed_qs_pairs or dynamic_query_params:
        parts: list[str] = []
        for k, v in fixed_qs_pairs:
            parts.append(f'"{k}": "{v}"')
        for n, _ in dynamic_query_params:
            parts.append(f'"{n}": {n}')
        items_str = ", ".join(parts)
        if dynamic_query_params:
            httpx_kwargs.append(
                f"params={{k: v for k, v in {{{items_str}}}.items() if v is not None}}"
            )
        else:
            httpx_kwargs.append(f"params={{{items_str}}}")

    if method in ("POST", "PUT"):
        if body_params:
            # Body parameters present: build a filtered dict comprehension
            # so that optional params set to None are not sent.
            items = ", ".join(f'"{n}": {n}' for n, _ in body_params)
            httpx_kwargs.append(f"data={{k: v for k, v in {{{items}}}.items() if v is not None}}")
        else:
            # No body parameters declared by ABB, but we still must send
            # Content-Type: application/x-www-form-urlencoded.
            # ABB RW6 returns HTTP 415 on any POST/PUT that lacks this
            # header, even when the body is empty.
            # Passing data={} causes httpx to set the header automatically.
            httpx_kwargs.append("data={}")

    method_lower = method.lower()
    success_code = parse_success_code(success_raw)

    # ── Rendering ─────────────────────────────────────────────────────────
    lines: list[str] = []

    if len(sig_parts) > 1:
        lines.append(f"async def {func_name}(")
        for part in sig_parts:
            lines.append(f"    {part},")
        lines.append(") -> httpx.Response:")
    else:
        lines.append(f"async def {func_name}({sig_parts[0]}) -> httpx.Response:")

    lines.append('    """')
    lines.append(f"    {title}.")
    lines.append("")

    # Route
    lines.extend(_wrap_doc(f"Route: ``{method} {url}``"))

    # ABB constraints
    if notes:
        notes_clean = notes.replace("\\", "/").replace("\n", " ").strip()
        if len(notes_clean) > 300:
            notes_clean = notes_clean[:297] + "..."
        lines.extend(_wrap_doc(f"ABB constraints: {notes_clean}"))

    lines.append("")
    lines.append("    Args:")
    lines.append("        client: Open RWSClient instance.")
    for p in path_params:
        lines.append(f"        {p}: URL path parameter.")
    for n, req in sorted(query_params, key=lambda x: not x[1]):
        if n in _url_qs_keys:
            continue
        req_str = "Required." if req else "Optional."
        lines.extend(_wrap_doc(f"{n}: Query parameter. {req_str}", indent="        "))
    for n, req in sorted(body_params, key=lambda x: not x[1]):
        req_str = "Required." if req else "Optional."
        lines.extend(_wrap_doc(f"{n}: Body parameter. {req_str}", indent="        "))

    lines.append("")
    lines.append("    Returns:")
    lines.append(f"        Raw HTTP response. Expected success: HTTP {success_code}.")
    lines.append("")
    lines.append("    Raises:")
    lines.append("        RWSAuthenticationError: On HTTP 401.")
    lines.append("        RWSNotFoundError: On HTTP 404.")
    lines.append("        RWSHTTPError: On any other HTTP >= 400.")

    if error_raw.strip():
        first_error = error_raw.splitlines()[0].strip().replace("\\", "/")
        lines.extend(_wrap_doc(f"# ABB codes: {first_error}", indent="        "))

    # ── Example ───────────────────────────────────────────────────────────
    lines.append("")
    lines.append("    Example:")
    lines.append("        ```python")

    example_args: list[str] = ["client"]
    for p in path_params:
        example_args.append(f'"{p}_value"')
    for n, req in query_params:
        if req and n not in _url_qs_keys:
            example_args.append(f'{n}="{n}_value"')
    for n, req in body_params:
        if req:
            example_args.append(f'{n}="{n}_value"')

    call_example = f"await {func_name}({', '.join(example_args)})"

    if len("        >>> " + call_example) <= _MAX_LINE:
        lines.append(f"        >>> {call_example}")
    else:
        paren_idx = call_example.index("(")
        func_part = call_example[: paren_idx + 1]
        ex_args = _split_dict_items(call_example[paren_idx + 1 : -1])
        lines.append(f"        >>> {func_part}")
        for i, arg in enumerate(ex_args):
            comma = "," if i < len(ex_args) - 1 else ""
            lines.append(f"        ...     {arg}{comma}")
        lines.append("        ... )")

    lines.append(f"        <Response [{success_code}]>")
    lines.append("        ```")
    lines.append('    """')

    # ── return statement ──────────────────────────────────────────────────
    lines.extend(_render_http_call(method_lower, url_expr, httpx_kwargs))

    return lines


# ---------------------------------------------------------------------------
# Test file generation
# ---------------------------------------------------------------------------


def render_tests(module_path: str, endpoints: list[dict]) -> str:
    """Generate the full content of a test file for an rws/ module.

    Args:
        module_path: Relative path (e.g. ``"rapid/execution"``).
        endpoints: List of endpoints for this module.

    Returns:
        Python test file content as a string.
    """
    module_import = module_path.replace("/", ".")
    # Utilise le même compteur que render_module → noms identiques
    func_names = _compute_func_names(endpoints)

    lines: list[str] = [
        "# This file is AUTO-GENERATED by utils/generator/main.py",
        "# DO NOT EDIT MANUALLY — run the generator to regenerate.",
        "#  Generator author: Clement RACINET",
        f'"""Auto-generated unit tests for rws/{module_path}."""',
        "from __future__ import annotations",
        "",
        "import httpx",
        "import pytest",
        "",
        "from abb_rws_client_python_rw6.core.client import RWSClient",
        f"from abb_rws_client_python_rw6.rws.{module_import} import (",
    ]
    for fn in sorted(func_names):  # trié alphabétiquement
        lines.append(f"    {fn},")
    lines.append(")")
    lines.append("")
    lines.append("")
    lines += [
        "class _MockTransport(httpx.AsyncBaseTransport):",
        '    """Mock transport returning a configurable HTTP response."""',
        "",
        '    def __init__(self, status_code: int = 200, content: bytes = b"") -> None:',
        "        self.status_code = status_code",
        "        self.content = content",
        "        self.last_request: httpx.Request | None = None",
        "",
        "    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:",
        "        self.last_request = request",
        "        return httpx.Response(self.status_code, content=self.content, request=request)",
        "",
        "",
        "def _make_client(transport: _MockTransport) -> RWSClient:",
        '    """Build an RWSClient connected to the mock transport."""',
        "    client = RWSClient.__new__(RWSClient)",
        "    client._http = httpx.AsyncClient(",
        "        transport=transport,",
        '        base_url="http://localhost/",',
        "    )",
        '    client.host = "localhost"',
        "    return client",
        "",
        "",
    ]

    for ep, func_name in zip(
        endpoints,
        func_names,
        strict=False,
    ):
        lines.extend(render_test_function(ep, func_name=func_name))
        lines.append("")

    return "\n".join(lines)


def render_test_function(ep: dict, *, func_name: str | None = None) -> list[str]:
    """Generate a pytest unit test for a single endpoint.

    Args:
        ep: Endpoint dictionary extracted from the ABB JSON.
        func_name: Pre-computed unique function name. If ``None``,
            ``endpoint_to_func_name`` is called without deduplication.

    Returns:
        List of Python lines.
    """
    if func_name is None:
        func_name = endpoint_to_func_name(ep)

    url: str = ep.get("url", "")
    method: str = ep.get("method", "GET").upper()
    success_raw: str = ep.get("success_response") or ""
    status_code = parse_success_code(success_raw)

    path_params = extract_path_params(url)
    query_params = parse_query_params(ep.get("url_params") or "")
    body_params = parse_body_params(ep.get("data_params") or "")

    url_path_only: str = url.split("?")[0]
    url_qs_only: str = url.split("?")[1] if "?" in url else ""

    fixed_qs: list[tuple[str, str]] = []
    if url_qs_only:
        for pair in url_qs_only.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    fixed_qs.append((k, v))
    fixed_qs_keys: set[str] = {k for k, _ in fixed_qs}

    dummy_path = ", ".join(f'"{p}_test"' for p in path_params)
    dummy_query_req = ", ".join(
        f'{n}="{n}_val"' for n, req in query_params if req and n not in fixed_qs_keys
    )
    dummy_body_req = ", ".join(f'{n}="{n}_val"' for n, req in body_params if req)
    all_dummy_kwargs = ", ".join(filter(None, [dummy_query_req, dummy_body_req]))

    call_args: list[str] = ["client"]
    if dummy_path:
        call_args.append(dummy_path)
    if all_dummy_kwargs:
        call_args.append(all_dummy_kwargs)
    call_str = f"await {func_name}({', '.join(call_args)})"

    expected_path = url_path_only
    for raw_p, py_p in zip(
        re.findall(r"\{([^}]+)\}", url_path_only),
        path_params,
        strict=False,
    ):
        expected_path = expected_path.replace(f"{{{raw_p}}}", f"{py_p}_test")
    if not expected_path.startswith("/"):
        expected_path = "/" + expected_path

    doc_text = f"Verify that {func_name} sends {method} {url}."
    doc_lines = _wrap_doc(doc_text, indent="    ")

    lines: list[str] = [
        "@pytest.mark.asyncio",
        f"async def test_{func_name}() -> None:",
        '    """',
    ]
    lines.extend(doc_lines)
    lines.append('    """')
    lines += [
        f"    transport = _MockTransport(status_code={status_code})",
        "    client = _make_client(transport)",
        "",
    ]
    lines.extend(_render_call_line(call_str))
    lines += [
        "",
        "    assert transport.last_request is not None",
        f'    assert transport.last_request.method == "{method}"',
    ]
    lines.extend(_render_path_assert(expected_path))

    for k, v in fixed_qs:
        lines.append(f'    assert transport.last_request.url.params["{k}"] == "{v}"')
    for n, req in query_params:
        if req and n not in fixed_qs_keys:
            lines.append(f'    assert transport.last_request.url.params["{n}"] == "{n}_val"')

    # POST/PUT must always carry Content-Type: application/x-www-form-urlencoded
    # (ABB RW6 returns 415 otherwise, even when the body is empty)
    if method in ("POST", "PUT"):
        lines += [
            '    ct = transport.last_request.headers.get("content-type") or ""',
            '    assert "application/x-www-form-urlencoded" in ct',
        ]

    lines.append(f"    assert resp.status_code == {status_code}")

    return lines


# ---------------------------------------------------------------------------
# __init__.py management  (inchangé)
# ---------------------------------------------------------------------------


def ensure_inits(modules: dict[str, list[dict]], dry_run: bool) -> None:
    """Create any missing ``__init__.py`` files in rws/ and tests/rws/.

    Args:
        modules: Dictionary ``{module_path: endpoints}``.
        dry_run: If True, print actions without writing any files.
    """
    dirs_to_init: set[Path] = {RWS_OUT, TESTS_OUT}

    for module_path in modules:
        parts = module_path.split("/")
        for depth in range(1, len(parts)):
            dirs_to_init.add(RWS_OUT / Path(*parts[:depth]))
            dirs_to_init.add(TESTS_OUT / Path(*parts[:depth]))

    for d in sorted(dirs_to_init):
        init = d / "__init__.py"
        if not init.exists():
            rel = d.relative_to(REPO_ROOT)
            rel_str = str(rel).replace("\\", "/")
            content = f'"""RWS sub-package: {rel_str}."""\n'
            if dry_run:
                print(f"  [DRY]  would create {rel_str}/__init__.py")
            else:
                d.mkdir(parents=True, exist_ok=True)
                init.write_text(content, encoding="utf-8")
                print(f"  [INIT] {rel_str}/__init__.py")


# ---------------------------------------------------------------------------
# Entry point  (inchangé)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Main entry point of the generator.

    Args:
        argv: CLI arguments (uses ``sys.argv`` if None).
    """
    parser = argparse.ArgumentParser(
        description="Generate abb_rws_client/rws/ from utils/scraping/abb_rws_api_full.json"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", metavar="MODULE", default=None)
    args = parser.parse_args(argv)

    if not API_JSON.exists():
        print(f"[ERROR] File not found: {API_JSON}", file=sys.stderr)
        sys.exit(1)

    raw: list[dict] = json.loads(API_JSON.read_text(encoding="utf-8"))
    print(f"[INFO] {len(raw)} entries read from {API_JSON.relative_to(REPO_ROOT)}")

    _apply_known_typo_fixes(raw)

    modules = group_by_module(raw)

    if args.only:
        if args.only not in modules:
            available = "\n  ".join(sorted(modules))
            print(
                f"[ERROR] Module '{args.only}' not found.\nAvailable:\n  {available}",
                file=sys.stderr,
            )
            sys.exit(1)
        modules = {args.only: modules[args.only]}

    ensure_inits(modules, dry_run=args.dry_run)

    for module_path, eps in sorted(modules.items()):
        rws_file = RWS_OUT / f"{module_path}.py"
        module_content = render_module(module_path, eps)

        if args.dry_run:
            print(f"  [DRY]  would write {rws_file.relative_to(REPO_ROOT)} ({len(eps)} endpoints)")
        else:
            rws_file.parent.mkdir(parents=True, exist_ok=True)
            rws_file.write_text(module_content, encoding="utf-8")
            print(f"  [GEN]  {rws_file.relative_to(REPO_ROOT)} ({len(eps)} endpoints)")

        module_parts = module_path.split("/")
        test_filename = f"test_{module_parts[-1]}.py"
        test_file = (
            TESTS_OUT / Path(*module_parts[:-1]) / test_filename
            if len(module_parts) > 1
            else TESTS_OUT / test_filename
        )
        test_content = render_tests(module_path, eps)

        if args.dry_run:
            print(f"  [DRY]  would write {test_file.relative_to(REPO_ROOT)}")
        else:
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(test_content, encoding="utf-8")
            print(f"  [TEST] {test_file.relative_to(REPO_ROOT)}")

    label = "Dry run" if args.dry_run else "Generation"
    print(f"\n[OK] {label} complete — {len(modules)} modules.")


if __name__ == "__main__":
    main()
