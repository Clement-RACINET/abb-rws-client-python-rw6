#!/usr/bin/env python3
# contrib/generator/main.py
"""
Source code generator for abb_rws_client/rws/.

Author: Clément RACINET

Reads  : contrib/scraping/abb_rws_api_full.json
Writes : abb_rws_client/rws/**/*.py
         tests/rws/**/*.py

This script is an internal development tool.
It is NOT part of the published library (pyproject.toml → packages = ["abb_rws_client"]).

Usage:
    python contrib/generator/main.py [--dry-run] [--only <module_path>]

Options:
    --dry-run          Print what would be generated without writing any files.
    --only <path>      Only generate the specified module (e.g. rapid/execution).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
API_JSON = REPO_ROOT / "contrib" / "scraping" / "abb_rws_api_full.json"
RWS_OUT = REPO_ROOT / "abb_rws_client" / "rws"
TESTS_OUT = REPO_ROOT / "tests" / "rws"

# ---------------------------------------------------------------------------
# Breadcrumb → Python module path mapping
#
# Principle: each level of the ABB breadcrumb is mapped to a Python file
# path relative to rws/.
#
# Examples:
#   ["Root Resource", "Get Service list"]
#       → rws/root.py                    tests/rws/test_root.py
#
#   ["RobotWare Services", "Mastership service", "..."]
#       → rws/mastership.py              tests/rws/test_mastership.py
#
#   ["RobotWare Services", "RAPID Service", "Operations on RAPID execution", "..."]
#       → rws/rapid/execution.py         tests/rws/rapid/test_execution.py
#
#   ["RobotWare Services", "IO Service", "Operations on IO Signals", "..."]
#       → rws/iosystem/signals.py        tests/rws/iosystem/test_signals.py
#
#   ["Controller Service", "Operations on Clock Resource", "..."]
#       → rws/ctrl/clock.py              tests/rws/ctrl/test_clock.py
#
#   ["User Service", "Operations on RMMP", "..."]
#       → rws/users/rmmp.py              tests/rws/users/test_rmmp.py
# ---------------------------------------------------------------------------

_ROUTING_TABLE: dict[str, str | dict] = {

    # ── Flat services ─────────────────────────────────────────────────────────
    "Root Resource": "root",
    "Subscription Service": "subscription",

    # ── User Service → rws/users/ ─────────────────────────────────────────────
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

    # ── Controller Service → rws/ctrl/ ────────────────────────────────────────
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

    # ── File Service → rws/fileservice.py (flat) ──────────────────────────────
    "File Service": "fileservice",

    # ── RobotWare Services → sub-folders per service ──────────────────────────
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

    # node is a dict → look up breadcrumb[1]
    level1 = breadcrumb[1]
    sub: str | dict | None = node.get(level1)  # type: ignore[union-attr]

    if sub is None:
        default: str = node.get("__default__", _slugify(level0))  # type: ignore[assignment]
        return default

    if isinstance(sub, str):
        return sub

    # sub is a dict → look up breadcrumb[2]
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
    print(
        f"[INFO] {total} endpoints → {len(result)} modules "
        f"({skipped} navigation nodes skipped)"
    )
    return result


# ---------------------------------------------------------------------------
# ABB parameter name sanitisation
# ---------------------------------------------------------------------------


def _sanitize_param_name(raw: str) -> str:
    """Convert an ABB parameter name to a valid Python identifier.

    ABB names may contain hyphens (e.g. ``domain-name``).

    Args:
        raw: Raw ABB name (e.g. ``"domain-name"``).

    Returns:
        Valid Python identifier (e.g. ``"domain_name"``).
    """
    name = re.sub(r"[^a-z0-9_]", "_", raw.lower())
    return re.sub(r"_+", "_", name).strip("_")


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

    Replaces ABB placeholders ``{domain-name}`` with sanitised Python
    identifiers ``{domain_name}``.

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
        py_name = re.sub(r"[^a-z0-9_]", "_", raw_name.lower())
        py_name = re.sub(r"_+", "_", py_name).strip("_")

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
        py_name = re.sub(r"[^a-z0-9_]", "_", raw_name.lower())
        py_name = re.sub(r"_+", "_", py_name).strip("_")

        if not py_name or py_name in seen:
            continue
        seen.add(py_name)

        is_required = bool(re.search(r"\bRequired\b", line, re.IGNORECASE))
        params.append((py_name, is_required))

    return params[:10]


# ---------------------------------------------------------------------------
# Function naming
# ---------------------------------------------------------------------------

_VERB_PREFIXES = frozenset({
    "get", "set", "post", "put", "delete", "create", "update",
    "start", "stop", "request", "release", "subscribe", "unsubscribe",
    "load", "save", "reset", "restart", "validate", "register",
    "login", "logout", "grant", "cancel", "poll", "add", "remove",
    "impersonate",
})


def endpoint_to_func_name(ep: dict) -> str:
    """Convert an endpoint to a snake_case Python function name.

    Uses the ABB ``title`` field. Prefixes with the HTTP method if the
    title does not already start with a recognised verb.

    Args:
        ep: Endpoint dictionary extracted from the ABB JSON.

    Returns:
        Valid Python function name (e.g. ``"get_execution_state"``).
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

    return func


# ---------------------------------------------------------------------------
# rws/ module generation
# ---------------------------------------------------------------------------


def render_module(module_path: str, endpoints: list[dict]) -> str:
    """Generate the full content of an rws/ module file.

    Note:
        The title extracted from the ABB breadcrumb is stripped of
        backslashes to prevent invalid escape sequences in the generated
        module docstring.

    Args:
        module_path: Relative path (e.g. ``"rapid/execution"``).
        endpoints: List of endpoints for this module.

    Returns:
        Python file content as a string.
    """
    first_bc = endpoints[0].get("breadcrumb", []) if endpoints else []
    title = " → ".join(first_bc[:3]) if first_bc else module_path
    # Strip any backslashes from ABB titles
    title = title.replace("\\", "/")

    lines: list[str] = [
        "# This file is AUTO-GENERATED by contrib/generator/main.py",
        "# DO NOT EDIT MANUALLY — run the generator to regenerate.",
        "#  Generator author: Clément RACINET",
        '"""',
        f"RWS module: {title}",
        "",
        "1:1 mirror of the ABB RobotWare 6 REST API.",
        "Each function maps to exactly one HTTP endpoint.",
        "No composed logic — see highlevel/ for wrappers.",
        '"""',
        "from __future__ import annotations",
        "",
        "import httpx",
        "",
        "from abb_rws_client._core.client import RWSClient",
        "",
        "",
    ]

    for ep in endpoints:
        lines.extend(render_function(ep))
        lines.append("")

    return "\n".join(lines)


def render_function(ep: dict) -> list[str]:
    """Generate the async function code for an ABB endpoint.

    Note:
        The ``notes`` and ``sample_call`` fields from the ABB JSON may
        contain backslashes (Windows paths, escaped URLs). These would be
        interpreted as Unicode escape sequences in the generated Python
        docstrings (e.g. ``\\U``, ``\\r``, ``\\t``) and cause a
        ``SyntaxError`` at import time. They are systematically replaced
        by forward slashes before being injected into the docstring.

        Required parameters are always placed before optional parameters
        in the signature to comply with the Python rule
        (non-default argument follows default argument).

    Args:
        ep: Endpoint dictionary extracted from the ABB JSON.

    Returns:
        List of Python lines (no trailing ``\\n``).
    """
    func_name = endpoint_to_func_name(ep)
    url: str = ep.get("url", "")
    method: str = ep.get("method", "GET").upper()
    title: str = ep.get("title", "")
    notes: str = (ep.get("notes") or "").strip()
    success_raw: str = ep.get("success_response") or ""
    error_raw: str = ep.get("error_response") or ""
    sample_raw: str = ep.get("sample_call") or ""

    path_params = extract_path_params(url)
    query_params = parse_query_params(ep.get("url_params") or "")
    body_params = parse_body_params(ep.get("data_params") or "")

    # ── Signature ─────────────────────────────────────────────────────────────
    # Python rule: parameters without defaults before parameters with defaults.
    sig_parts: list[str] = ["client: RWSClient"]
    # Path parameters (always required)
    sig_parts += [f"{p}: str" for p in path_params]
    # Required first, optional second
    # Exclude params already fixed in the ABB URL query string
    _url_qs_keys = {
        pair.split("=")[0].strip()
        for pair in (url.split("?")[1] if "?" in url else "").split("&")
        if "=" in pair
    }
    query_required = [f"{n}: str" for n, req in query_params if req and n not in _url_qs_keys]
    query_optional = [f"{n}: str | None = None" for n, req in query_params if not req and n not in _url_qs_keys]

    body_required = [f"{n}: str" for n, req in body_params if req]
    body_optional = [f"{n}: str | None = None" for n, req in body_params if not req]
    sig_parts += query_required + body_required + query_optional + body_optional

    # ── Split ABB URL path from query string ──────────────────────────────────
    # e.g. "/ctrl/clock/timezone?action=show"
    #   → url_path = "/ctrl/clock/timezone"
    #   → url_qs   = "action=show"
    url_path = url.split("?")[0]
    url_qs = url.split("?")[1] if "?" in url else ""

    # ── Python URL expression (path only) ─────────────────────────────────────
    url_expr = build_url_expr(url_path)

    # ── httpx kwargs ──────────────────────────────────────────────────────────
    httpx_kwargs: list[str] = []

    # Build the params dict by merging:
    # 1. Fixed params from the ABB URL query string (e.g. action=show)
    # 2. Dynamic params from the ABB url_params field
    fixed_qs_pairs: list[tuple[str, str]] = []
    if url_qs:
        for pair in url_qs.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    fixed_qs_pairs.append((k, v))

    # Keys already covered by the fixed ABB URL query string
    fixed_qs_keys_func: set[str] = {k for k, _ in fixed_qs_pairs}

    # Dynamic params: exclude those already in the fixed QS
    dynamic_query_params = [(n, req) for n, req in query_params if n not in fixed_qs_keys_func]

    if fixed_qs_pairs or dynamic_query_params:
        parts: list[str] = []
        # Fixed params (literal value)
        for k, v in fixed_qs_pairs:
            parts.append(f'"{k}": "{v}"')
        # Dynamic params (Python variable)
        for n, _ in dynamic_query_params:
            parts.append(f'"{n}": {n}')
        items_str = ", ".join(parts)
        if dynamic_query_params:
            # Filter out None values for optional dynamic params
            httpx_kwargs.append(
                f"params={{k: v for k, v in {{{items_str}}}.items() if v is not None}}"
            )
        else:
            # Only fixed params → literal dict, no None filter needed
            httpx_kwargs.append(f"params={{{items_str}}}")

    if body_params and method in ("POST", "PUT"):
        items = ", ".join(f'"{n}": {n}' for n, _ in body_params)
        httpx_kwargs.append(
            f"data={{k: v for k, v in {{{items}}}.items() if v is not None}}"
        )

    kwargs_str = ", ".join(httpx_kwargs)
    method_lower = method.lower()
    http_call = (
        f"await client.{method_lower}({url_expr}, {kwargs_str})"
        if kwargs_str
        else f"await client.{method_lower}({url_expr})"
    )

    # ── Rendering ─────────────────────────────────────────────────────────────
    lines: list[str] = []

    if len(sig_parts) > 1:
        lines.append(f"async def {func_name}(")
        for part in sig_parts:
            lines.append(f"    {part},")
        lines.append(") -> httpx.Response:")
    else:
        lines.append(f"async def {func_name}({sig_parts[0]}) -> httpx.Response:")

    success_code = parse_success_code(success_raw)
    lines.append('    """')
    lines.append(f"    {title}.")
    lines.append("")
    lines.append(f"    Route: ``{method} {url}``")

    if notes:
        # Mandatory cleanup: backslashes in raw ABB data break Python docstrings
        # (\U, \r, \t → SyntaxError at import time).
        notes_clean = notes.replace("\\", "/").replace("\n", " ").strip()
        if len(notes_clean) > 300:
            notes_clean = notes_clean[:297] + "..."
        lines.append(f"    ABB constraints: {notes_clean}")

    lines.append("")
    lines.append("    Args:")
    lines.append("        client: Open RWSClient instance.")
    for p in path_params:
        lines.append(f"        {p}: URL path parameter.")
    # Docstring: same order as signature (required then optional)
    # Exclude fixed QS params from ABB (not part of the function signature)
    for n, req in sorted(query_params, key=lambda x: not x[1]):
        if n in _url_qs_keys:
            continue
        req_str = "Required." if req else "Optional."
        lines.append(f"        {n}: Query parameter. {req_str}")
    for n, req in sorted(body_params, key=lambda x: not x[1]):
        req_str = "Required." if req else "Optional."
        lines.append(f"        {n}: Body parameter. {req_str}")

    lines.append("")
    lines.append("    Returns:")
    lines.append(f"        Raw HTTP response. Expected success: HTTP {success_code}.")
    lines.append("")
    lines.append("    Raises:")
    lines.append("        RWSAuthenticationError: On HTTP 401.")
    lines.append("        RWSNotFoundError: On HTTP 404.")
    lines.append("        RWSHTTPError: On any other HTTP >= 400.")

    if error_raw.strip():
        first_error = error_raw.splitlines()[0].strip()
        first_error = first_error.replace("\\", "/")
        lines.append(f"        # ABB codes: {first_error}")

    if sample_raw.strip():
        first_sample = sample_raw.strip().splitlines()[0][:120]
        first_sample = first_sample.replace("\\", "/")
        lines.append("")
        lines.append("    Example:")
        lines.append(f"        # {first_sample}")

    lines.append('    """')
    lines.append(f"    return {http_call}")

    return lines


# ---------------------------------------------------------------------------
# Test file generation
# ---------------------------------------------------------------------------


def render_tests(module_path: str, endpoints: list[dict]) -> str:
    """Generate the full content of a test file for an rws/ module.

    The test file path mirrors rws/:
    ``rws/rapid/execution.py`` → ``tests/rws/rapid/test_execution.py``

    Args:
        module_path: Relative path (e.g. ``"rapid/execution"``).
        endpoints: List of endpoints for this module.

    Returns:
        Python test file content as a string.
    """
    module_import = module_path.replace("/", ".")
    func_names = [endpoint_to_func_name(ep) for ep in endpoints]

    lines: list[str] = [
        "# This file is AUTO-GENERATED by contrib/generator/main.py",
        "# DO NOT EDIT MANUALLY — run the generator to regenerate.",
        "#  Generator author: Clément RACINET",
        f'"""Auto-generated unit tests for rws/{module_path}."""',
        "from __future__ import annotations",
        "",
        "import pytest",
        "import httpx",
        "",
        "from abb_rws_client._core.client import RWSClient",
        f"from abb_rws_client.rws.{module_import} import (",
    ]
    for fn in func_names:
        lines.append(f"    {fn},")
    lines.append(")")
    lines.append("")
    lines.append("")
    lines += [
        "class _MockTransport(httpx.AsyncBaseTransport):",
        '    """Mock transport returning a configurable HTTP response."""',
        "",
        "    def __init__(self, status_code: int = 200, content: bytes = b\"\") -> None:",
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

    for ep in endpoints:
        lines.extend(render_test_function(ep))
        lines.append("")

    return "\n".join(lines)


def render_test_function(ep: dict) -> list[str]:
    """Generate a pytest unit test for a single endpoint.

    Note:
        ABB URLs may embed a query string directly in the ``url`` field
        (e.g. ``/ctrl/clock/timezone?action=show``). The path and query
        string are split before generation so that ``url.path`` never
        contains ``?...``.
        Fixed query string params from the ABB URL are asserted with their
        literal value; dynamic params are asserted with their test value.

    Args:
        ep: Endpoint dictionary extracted from the ABB JSON.

    Returns:
        List of Python lines.
    """
    func_name = endpoint_to_func_name(ep)
    url: str = ep.get("url", "")
    method: str = ep.get("method", "GET").upper()
    success_raw: str = ep.get("success_response") or ""
    status_code = parse_success_code(success_raw)

    path_params = extract_path_params(url)
    query_params = parse_query_params(ep.get("url_params") or "")
    body_params = parse_body_params(ep.get("data_params") or "")

    # ── Split ABB URL path from query string ──────────────────────────────────
    url_path_only: str = url.split("?")[0]
    url_qs_only: str = url.split("?")[1] if "?" in url else ""

    # Fixed params from the ABB query string (e.g. action=show)
    fixed_qs: list[tuple[str, str]] = []
    if url_qs_only:
        for pair in url_qs_only.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    fixed_qs.append((k, v))
    fixed_qs_keys: set[str] = {k for k, _ in fixed_qs}

    # ── Call arguments ────────────────────────────────────────────────────────
    dummy_path = ", ".join(f'"{p}_test"' for p in path_params)
    # Fixed ABB QS params are NOT function arguments
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

    # ── Expected path (path only, test values injected) ───────────────────────
    expected_path = url_path_only
    for raw_p, py_p in zip(
        re.findall(r"\{([^}]+)\}", url_path_only),
        path_params,
    ):
        expected_path = expected_path.replace(f"{{{raw_p}}}", f"{py_p}_test")
    if not expected_path.startswith("/"):
        expected_path = "/" + expected_path

    # ── Line generation ───────────────────────────────────────────────────────
    lines: list[str] = [
        "@pytest.mark.asyncio",
        f"async def test_{func_name}() -> None:",
        f'    """Verify that {func_name} sends {method} {url}."""',
        f"    transport = _MockTransport(status_code={status_code})",
        "    client = _make_client(transport)",
        "",
        f"    resp = {call_str}",
        "",
        "    assert transport.last_request is not None",
        f'    assert transport.last_request.method == "{method}"',
        f'    assert transport.last_request.url.path == "{expected_path}"',
    ]

    # ── Query param assertions via .params["key"] ─────────────────────────────
    # 1. Fixed ABB QS params → exact literal value
    for k, v in fixed_qs:
        lines.append(
            f'    assert transport.last_request.url.params["{k}"] == "{v}"'
        )
    # 2. Required dynamic params → test value
    for n, req in query_params:
        if req and n not in fixed_qs_keys:
            lines.append(
                f'    assert transport.last_request.url.params["{n}"] == "{n}_val"'
            )

    lines.append(f"    assert resp.status_code == {status_code}")

    return lines


# ---------------------------------------------------------------------------
# __init__.py management
# ---------------------------------------------------------------------------


def ensure_inits(modules: dict[str, list[dict]], dry_run: bool) -> None:
    """Create any missing ``__init__.py`` files in rws/ and tests/rws/.

    Walks all intermediate directories that are required.

    Note:
        Paths are normalised to forward slashes (``/``) to prevent Windows
        path separators (``\\``) from being interpreted as Unicode escape
        sequences in generated docstrings
        (e.g. ``tests\\users`` → ``\\u`` → ``SyntaxError``).

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
            # Mandatory normalisation on Windows:
            # Path.relative_to() returns "tests\rws\users" with backslashes.
            # In a Python docstring, \u, \r, \t are escape sequences
            # → SyntaxError at import time. Force forward slashes.
            rel_str = str(rel).replace("\\", "/")
            content = f'"""RWS sub-package: {rel_str}."""\n'
            if dry_run:
                print(f"  [DRY]  would create {rel_str}/__init__.py")
            else:
                d.mkdir(parents=True, exist_ok=True)
                init.write_text(content, encoding="utf-8")
                print(f"  [INIT] {rel_str}/__init__.py")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Main entry point of the generator.

    Args:
        argv: CLI arguments (uses ``sys.argv`` if None).
    """
    parser = argparse.ArgumentParser(
        description="Generate abb_rws_client/rws/ from contrib/scraping/abb_rws_api_full.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be generated without writing any files.",
    )
    parser.add_argument(
        "--only",
        metavar="MODULE",
        default=None,
        help="Only generate this module (e.g. rapid/execution).",
    )
    args = parser.parse_args(argv)

    # ── Read JSON ─────────────────────────────────────────────────────────────
    if not API_JSON.exists():
        print(f"[ERROR] File not found: {API_JSON}", file=sys.stderr)
        print(
            "        Run contrib/scraping/scrape.py first to generate this file.",
            file=sys.stderr,
        )
        sys.exit(1)

    raw: list[dict] = json.loads(API_JSON.read_text(encoding="utf-8"))
    print(f"[INFO] {len(raw)} entries read from {API_JSON.relative_to(REPO_ROOT)}")

    # ── Grouping ──────────────────────────────────────────────────────────────
    modules = group_by_module(raw)

    if args.only:
        if args.only not in modules:
            available = "\n  ".join(sorted(modules))
            print(
                f"[ERROR] Module '{args.only}' not found.\n"
                f"Available modules:\n  {available}",
                file=sys.stderr,
            )
            sys.exit(1)
        modules = {args.only: modules[args.only]}

    # ── Generation ────────────────────────────────────────────────────────────
    ensure_inits(modules, dry_run=args.dry_run)

    for module_path, eps in sorted(modules.items()):
        # ── rws/ module ───────────────────────────────────────────────────────
        rws_file = RWS_OUT / f"{module_path}.py"
        module_content = render_module(module_path, eps)

        if args.dry_run:
            print(
                f"  [DRY]  would write {rws_file.relative_to(REPO_ROOT)}"
                f" ({len(eps)} endpoints)"
            )
        else:
            rws_file.parent.mkdir(parents=True, exist_ok=True)
            rws_file.write_text(module_content, encoding="utf-8")
            print(
                f"  [GEN]  {rws_file.relative_to(REPO_ROOT)}"
                f" ({len(eps)} endpoints)"
            )

        # ── Tests: mirror of rws/ ─────────────────────────────────────────────
        # rws/rapid/execution.py  →  tests/rws/rapid/test_execution.py
        # rws/mastership.py       →  tests/rws/test_mastership.py
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

    print(
        f"\n[OK] {'Dry run' if args.dry_run else 'Generation'} complete — "
        f"{len(modules)} modules."
    )


if __name__ == "__main__":
    main()
