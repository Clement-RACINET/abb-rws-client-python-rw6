#!/usr/bin/env python3
# contrib/generator/main.py
"""
Générateur de code source pour abb_rws_client/rws/.

Lit    : contrib/scraping/abb_rws_api_full.json
Écrit  : abb_rws_client/rws/**/*.py
         tests/rws/**/*.py

Ce script est un outil de développement interne.
Il ne fait PAS partie de la bibliothèque publiée (pyproject.toml → packages = ["abb_rws_client"]).

Usage:
    python contrib/generator/main.py [--dry-run] [--only <module_path>]

Options:
    --dry-run          Affiche ce qui serait généré sans écrire de fichiers.
    --only <path>      Ne génère que le module indiqué (ex: rapid/execution).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
API_JSON = REPO_ROOT / "contrib" / "scraping" / "abb_rws_api_full.json"
RWS_OUT = REPO_ROOT / "abb_rws_client" / "rws"
TESTS_OUT = REPO_ROOT / "tests" / "rws"

# ---------------------------------------------------------------------------
# Mapping breadcrumb → chemin de module Python
#
# Principe : on mappe chaque niveau du breadcrumb ABB vers un chemin
# de fichier Python relatif à rws/.
#
# Exemples :
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

    # ── Services plats ────────────────────────────────────────────────────────
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

    # ── File Service → rws/fileservice.py (plat) ──────────────────────────────
    "File Service": "fileservice",

    # ── RobotWare Services → sous-dossiers selon le service ───────────────────
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
    """Résout le chemin de module Python (relatif à rws/) depuis un breadcrumb ABB.

    Parcourt ``_ROUTING_TABLE`` niveau par niveau.
    Retourne ``None`` pour les nœuds de navigation sans endpoint.

    Args:
        breadcrumb: Liste de chaînes extraite du JSON ABB.

    Returns:
        Chemin relatif (ex: ``"rapid/execution"``, ``"users/rmmp"``)
        ou ``None`` si le nœud est une page de navigation.
    """
    if not breadcrumb or len(breadcrumb) < 2:
        return None

    level0 = breadcrumb[0]
    node: str | dict | None = _ROUTING_TABLE.get(level0)

    if node is None:
        return _slugify(level0)

    if isinstance(node, str):
        return node

    # node est un dict → chercher breadcrumb[1]
    level1 = breadcrumb[1]
    sub: str | dict | None = node.get(level1)  # type: ignore[union-attr]

    if sub is None:
        default: str = node.get("__default__", _slugify(level0))  # type: ignore[assignment]
        return default

    if isinstance(sub, str):
        return sub

    # sub est un dict → chercher breadcrumb[2]
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
    """Convertit un nom ABB en slug Python valide (snake_case).

    Args:
        text: Texte brut (ex: ``"IO Service"``).

    Returns:
        Slug (ex: ``"io_service"``).
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s_]", "", slug)
    slug = re.sub(r"\s+", "_", slug).strip("_")
    return slug


# ---------------------------------------------------------------------------
# Groupement des endpoints par module
# ---------------------------------------------------------------------------


def group_by_module(endpoints: list[dict]) -> dict[str, list[dict]]:
    """Regroupe les endpoints par chemin de module Python.

    Filtre les nœuds sans URL ou sans méthode HTTP (pages de navigation).

    Args:
        endpoints: Liste brute du JSON ABB.

    Returns:
        Dictionnaire ``{module_path: [endpoint, ...]}``.
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
        f"({skipped} nœuds de navigation ignorés)"
    )
    return result


# ---------------------------------------------------------------------------
# Sanitisation des noms de paramètres ABB
# ---------------------------------------------------------------------------


def _sanitize_param_name(raw: str) -> str:
    """Convertit un nom de paramètre ABB en identifiant Python valide.

    Les noms ABB peuvent contenir des tirets (ex: ``domain-name``).

    Args:
        raw: Nom brut ABB (ex: ``"domain-name"``).

    Returns:
        Identifiant Python valide (ex: ``"domain_name"``).
    """
    name = re.sub(r"[^a-z0-9_]", "_", raw.lower())
    return re.sub(r"_+", "_", name).strip("_")


def extract_path_params(url: str) -> list[str]:
    """Extrait et sanitise les paramètres de chemin ``{param}`` d'une URL ABB.

    Args:
        url: URL ABB (ex: ``/rw/mastership/{domain-name}``).

    Returns:
        Noms sanitisés (ex: ``["domain_name"]``).
    """
    return [_sanitize_param_name(p) for p in re.findall(r"\{([^}]+)\}", url)]


def build_url_expr(url: str) -> str:
    """Construit l'expression Python pour l'URL (str littérale ou f-string).

    Remplace les placeholders ABB ``{domain-name}`` par les identifiants
    Python sanitisés ``{domain_name}``.

    Args:
        url: URL ABB brute (ex: ``"/rw/mastership/{domain-name}"``).

    Returns:
        Expression Python (ex: ``'f"/rw/mastership/{domain_name}"'``).
    """
    raw_params = re.findall(r"\{([^}]+)\}", url)
    if not raw_params:
        return f'"{url}"'

    py_url = url
    for raw in raw_params:
        py_url = py_url.replace(f"{{{raw}}}", f"{{{_sanitize_param_name(raw)}}}")

    return f'f"{py_url}"'


# ---------------------------------------------------------------------------
# Parsing des paramètres ABB
# ---------------------------------------------------------------------------


def parse_success_code(success_raw: str) -> int:
    """Extrait le premier code HTTP de succès depuis la description ABB.

    Args:
        success_raw: Chaîne brute (ex: ``"HTTP_OK(200), see HTTP Status codes"``).

    Returns:
        Code HTTP entier. Défaut : 200.
    """
    match = re.search(r"\b(200|201|202|204)\b", success_raw or "")
    return int(match.group(1)) if match else 200


def parse_query_params(url_params_raw: str) -> list[tuple[str, bool]]:
    """Extrait les paramètres query depuis le champ ``url_params`` ABB.

    Args:
        url_params_raw: Contenu brut du champ ``url_params``.

    Returns:
        Liste de ``(nom_python, is_required)``.
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
    """Extrait les paramètres body depuis le champ ``data_params`` ABB.

    Args:
        data_params_raw: Contenu brut du champ ``data_params``.

    Returns:
        Liste de ``(nom_python, is_required)``.
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
# Nommage des fonctions
# ---------------------------------------------------------------------------

_VERB_PREFIXES = frozenset({
    "get", "set", "post", "put", "delete", "create", "update",
    "start", "stop", "request", "release", "subscribe", "unsubscribe",
    "load", "save", "reset", "restart", "validate", "register",
    "login", "logout", "grant", "cancel", "poll", "add", "remove",
    "impersonate",
})


def endpoint_to_func_name(ep: dict) -> str:
    """Convertit un endpoint en nom de fonction Python snake_case.

    Utilise le ``title`` ABB. Préfixe avec la méthode HTTP si le titre
    ne commence pas déjà par un verbe reconnu.

    Args:
        ep: Dictionnaire d'un endpoint extrait du JSON ABB.

    Returns:
        Nom de fonction valide Python (ex: ``"get_execution_state"``).
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
# Génération du module rws/
# ---------------------------------------------------------------------------


def render_module(module_path: str, endpoints: list[dict]) -> str:
    """Génère le contenu complet d'un module rws/.

    Note:
        Le titre extrait du breadcrumb ABB est nettoyé des backslashes
        pour éviter des séquences d'échappement invalides dans le module
        docstring généré.

    Args:
        module_path: Chemin relatif (ex: ``"rapid/execution"``).
        endpoints: Liste des endpoints de ce module.

    Returns:
        Contenu Python du fichier en tant que chaîne.
    """
    first_bc = endpoints[0].get("breadcrumb", []) if endpoints else []
    title = " → ".join(first_bc[:3]) if first_bc else module_path
    # Nettoyage des backslashes éventuels dans les titres ABB
    title = title.replace("\\", "/")

    lines: list[str] = [
        "# This file is AUTO-GENERATED by contrib/generator/main.py",
        "# DO NOT EDIT MANUALLY — run the generator to regenerate.",
        '"""',
        f"RWS module : {title}",
        "",
        "Miroir 1:1 de l'API REST ABB RobotWare 6.",
        "Chaque fonction correspond à exactement un endpoint HTTP.",
        "Aucune logique composée — voir highlevel/ pour les wrappers.",
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
    """Génère le code d'une fonction async pour un endpoint ABB.

    Note:
        Les champs ``notes`` et ``sample_call`` du JSON ABB peuvent contenir
        des backslashes (chemins Windows, URLs échappées). Ces backslashes
        seraient interprétés comme des séquences d'échappement Unicode dans
        les docstrings Python générées (ex: ``\\U``, ``\\r``, ``\\t``)
        → ``SyntaxError`` à l'import. Ils sont systématiquement remplacés
        par des forward slashes avant injection dans la docstring.

        Les paramètres requis sont toujours placés avant les paramètres
        optionnels dans la signature pour respecter la règle Python
        (non-default argument follows default argument).

    Args:
        ep: Dictionnaire d'un endpoint extrait du JSON ABB.

    Returns:
        Liste de lignes Python (sans ``\\n`` terminal).
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
    # Règle Python : paramètres sans défaut avant paramètres avec défaut.
    sig_parts: list[str] = ["client: RWSClient"]
    # Paramètres de chemin (toujours requis)
    sig_parts += [f"{p}: str" for p in path_params]
    # Requis d'abord, optionnels ensuite
    query_required = [f"{n}: str" for n, req in query_params if req]
    query_optional = [f"{n}: str | None = None" for n, req in query_params if not req]
    body_required = [f"{n}: str" for n, req in body_params if req]
    body_optional = [f"{n}: str | None = None" for n, req in body_params if not req]
    sig_parts += query_required + body_required + query_optional + body_optional

    # ── URL Python ────────────────────────────────────────────────────────────
    url_expr = build_url_expr(url)

    # ── kwargs httpx ──────────────────────────────────────────────────────────
    httpx_kwargs: list[str] = []

    if query_params:
        items = ", ".join(f'"{n}": {n}' for n, _ in query_params)
        httpx_kwargs.append(
            f"params={{k: v for k, v in {{{items}}}.items() if v is not None}}"
        )

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

    # ── Rendu ─────────────────────────────────────────────────────────────────
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
        # Nettoyage obligatoire : les backslashes dans les données ABB brutes
        # cassent les docstrings Python (\U, \r, \t → SyntaxError).
        notes_clean = notes.replace("\\", "/").replace("\n", " ").strip()
        if len(notes_clean) > 300:
            notes_clean = notes_clean[:297] + "..."
        lines.append(f"    Contraintes ABB: {notes_clean}")

    lines.append("")
    lines.append("    Args:")
    lines.append("        client: Instance RWSClient ouverte.")
    for p in path_params:
        lines.append(f"        {p}: Paramètre de chemin URL.")
    # Docstring : même ordre que la signature (requis puis optionnels)
    for n, req in sorted(query_params, key=lambda x: not x[1]):
        req_str = "Requis." if req else "Optionnel."
        lines.append(f"        {n}: Paramètre query. {req_str}")
    for n, req in sorted(body_params, key=lambda x: not x[1]):
        req_str = "Requis." if req else "Optionnel."
        lines.append(f"        {n}: Paramètre body. {req_str}")

    lines.append("")
    lines.append("    Returns:")
    lines.append(f"        Réponse HTTP brute. Succès attendu : HTTP {success_code}.")
    lines.append("")
    lines.append("    Raises:")
    lines.append("        RWSAuthenticationError: Sur HTTP 401.")
    lines.append("        RWSNotFoundError: Sur HTTP 404.")
    lines.append("        RWSHTTPError: Sur tout autre HTTP >= 400.")

    if error_raw.strip():
        first_error = error_raw.splitlines()[0].strip()
        first_error = first_error.replace("\\", "/")
        lines.append(f"        # Codes ABB: {first_error}")

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
# Génération des tests
# ---------------------------------------------------------------------------


def render_tests(module_path: str, endpoints: list[dict]) -> str:
    """Génère le contenu complet d'un fichier de tests pour un module rws/.

    Le chemin du fichier de test est un miroir de rws/ :
    ``rws/rapid/execution.py`` → ``tests/rws/rapid/test_execution.py``

    Args:
        module_path: Chemin relatif (ex: ``"rapid/execution"``).
        endpoints: Liste des endpoints de ce module.

    Returns:
        Contenu Python du fichier de tests en tant que chaîne.
    """
    module_import = module_path.replace("/", ".")
    func_names = [endpoint_to_func_name(ep) for ep in endpoints]

    lines: list[str] = [
        "# This file is AUTO-GENERATED by contrib/generator/main.py",
        "# DO NOT EDIT MANUALLY — run the generator to regenerate.",
        f'"""Tests unitaires auto-générés pour rws/{module_path}."""',
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
        '    """Transport mock retournant une réponse HTTP configurable."""',
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
        '    """Construit un RWSClient branché sur le transport mock."""',
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
    """Génère un test unitaire pytest pour un endpoint.

    Les assertions utilisent ``url.path`` et ``url.params["key"]``
    plutôt que ``str(url)`` pour être robustes à l'encodage httpx.

    Args:
        ep: Dictionnaire d'un endpoint extrait du JSON ABB.

    Returns:
        Liste de lignes Python.
    """
    func_name = endpoint_to_func_name(ep)
    url: str = ep.get("url", "")
    method: str = ep.get("method", "GET").upper()
    success_raw: str = ep.get("success_response") or ""
    status_code = parse_success_code(success_raw)

    path_params = extract_path_params(url)
    query_params = parse_query_params(ep.get("url_params") or "")
    body_params = parse_body_params(ep.get("data_params") or "")

    # ── Arguments d'appel ─────────────────────────────────────────────────────
    dummy_path = ", ".join(f'"{p}_test"' for p in path_params)
    dummy_query_req = ", ".join(f'{n}="{n}_val"' for n, req in query_params if req)
    dummy_body_req = ", ".join(f'{n}="{n}_val"' for n, req in body_params if req)
    all_dummy_kwargs = ", ".join(filter(None, [dummy_query_req, dummy_body_req]))

    call_args: list[str] = ["client"]
    if dummy_path:
        call_args.append(dummy_path)
    if all_dummy_kwargs:
        call_args.append(all_dummy_kwargs)
    call_str = f"await {func_name}({', '.join(call_args)})"

    # ── Chemin URL attendu (avec valeurs de test injectées) ───────────────────
    # On remplace {param-name} par param_name_test (version sanitisée + _test)
    expected_path = url
    for raw_p, py_p in zip(
        re.findall(r"\{([^}]+)\}", url),
        path_params,
    ):
        expected_path = expected_path.replace(f"{{{raw_p}}}", f"{py_p}_test")
    if not expected_path.startswith("/"):
        expected_path = "/" + expected_path

    # ── Génération des lignes ─────────────────────────────────────────────────
    lines: list[str] = [
        "@pytest.mark.asyncio",
        f"async def test_{func_name}() -> None:",
        f'    """Vérifie que {func_name} émet {method} {url}."""',
        f"    transport = _MockTransport(status_code={status_code})",
        "    client = _make_client(transport)",
        "",
        f"    resp = {call_str}",
        "",
        "    assert transport.last_request is not None",
        f'    assert transport.last_request.method == "{method}"',
        f'    assert transport.last_request.url.path == "{expected_path}"',
    ]

    # Assertions sur les query params requis — via .params["key"] (robuste)
    for n, req in query_params:
        if req:
            lines.append(
                f'    assert transport.last_request.url.params["{n}"] == "{n}_val"'
            )

    lines.append(f"    assert resp.status_code == {status_code}")

    return lines


# ---------------------------------------------------------------------------
# Gestion des __init__.py
# ---------------------------------------------------------------------------


def ensure_inits(modules: dict[str, list[dict]], dry_run: bool) -> None:
    """Crée les ``__init__.py`` manquants dans rws/ et tests/rws/.

    Parcourt tous les dossiers intermédiaires nécessaires.

    Note:
        Les chemins sont normalisés avec des slashes forward (``/``) pour
        éviter que les séparateurs Windows (``\\``) soient interprétés comme
        des séquences d'échappement Unicode dans les docstrings générées
        (ex: ``tests\\users`` → ``\\u`` → ``SyntaxError``).

    Args:
        modules: Dictionnaire ``{module_path: endpoints}``.
        dry_run: Si True, affiche sans écrire.
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
            # Normalisation obligatoire sur Windows :
            # Path.relative_to() retourne "tests\rws\users" avec des backslashes.
            # Dans une docstring Python, \u, \r, \t sont des séquences d'échappement
            # → SyntaxError à l'import. On force les forward slashes.
            rel_str = str(rel).replace("\\", "/")
            content = f'"""RWS sub-package: {rel_str}."""\n'
            if dry_run:
                print(f"  [DRY]  would create {rel_str}/__init__.py")
            else:
                d.mkdir(parents=True, exist_ok=True)
                init.write_text(content, encoding="utf-8")
                print(f"  [INIT] {rel_str}/__init__.py")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Point d'entrée principal du générateur.

    Args:
        argv: Arguments CLI (utilise ``sys.argv`` si None).
    """
    parser = argparse.ArgumentParser(
        description="Génère abb_rws_client/rws/ depuis contrib/scraping/abb_rws_api_full.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche ce qui serait généré sans écrire de fichiers.",
    )
    parser.add_argument(
        "--only",
        metavar="MODULE",
        default=None,
        help="Ne génère que ce module (ex: rapid/execution).",
    )
    args = parser.parse_args(argv)

    # ── Lecture du JSON ───────────────────────────────────────────────────────
    if not API_JSON.exists():
        print(f"[ERROR] Fichier introuvable : {API_JSON}", file=sys.stderr)
        print(
            "        Lancez d'abord contrib/scraping/scrape.py pour générer ce fichier.",
            file=sys.stderr,
        )
        sys.exit(1)

    raw: list[dict] = json.loads(API_JSON.read_text(encoding="utf-8"))
    print(f"[INFO] {len(raw)} entrées lues depuis {API_JSON.relative_to(REPO_ROOT)}")

    # ── Groupement ────────────────────────────────────────────────────────────
    modules = group_by_module(raw)

    if args.only:
        if args.only not in modules:
            available = "\n  ".join(sorted(modules))
            print(
                f"[ERROR] Module '{args.only}' introuvable.\n"
                f"Modules disponibles :\n  {available}",
                file=sys.stderr,
            )
            sys.exit(1)
        modules = {args.only: modules[args.only]}

    # ── Génération ────────────────────────────────────────────────────────────
    ensure_inits(modules, dry_run=args.dry_run)

    for module_path, eps in sorted(modules.items()):
        # ── Module rws/ ───────────────────────────────────────────────────────
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

        # ── Tests : miroir de rws/ ─────────────────────────────────────────────
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
        f"\n[OK] {'Simulation' if args.dry_run else 'Génération'} terminée — "
        f"{len(modules)} modules."
    )


if __name__ == "__main__":
    main()
