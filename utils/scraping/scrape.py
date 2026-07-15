#!/usr/bin/env python3
# utils/scraping/scrape.py
"""
ABB RobotWare 6 RWS API scraper.

Author: Clement RACINET

Crawls the ABB Developer Center Doxygen documentation and extracts all
RWS REST API endpoints into structured JSON and Markdown files.

Reads  : https://developercenter.robotstudio.com/api/rwsApi/
Writes : utils/scraping/abb_rws_api_full.json
         utils/scraping/abb_rws_api_full.md
         utils/scraping/routes_list.json  (crawl cache)
         utils/scraping/scrape.log

Usage:
    python utils/scraping/scrape.py

Notes:
    - If ``routes_list.json`` already exists, the crawl phase (Phase 1)
      is skipped and the cached route list is used directly.
    - Delete ``routes_list.json`` to force a full re-crawl.
"""

import json
import logging
from pathlib import Path
import re
import sys
import time

from bs4 import BeautifulSoup, Tag
import requests

# ============================================================
#  Paths
# ============================================================

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

ROUTES_FILE = SCRIPT_DIR / "routes_list.json"
LOG_FILE = SCRIPT_DIR / "scrape.log"

# ============================================================
#  Logger
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ============================================================
#  Configuration
# ============================================================

BASE_URL: str = "https://developercenter.robotstudio.com/api/rwsApi/"

#: Set of already-visited .js URLs (deduplication guard)
VISITED_JS: set[str] = set()

#: Accumulated list of discovered routes
ROUTES: list[dict] = []

#: Root navigation tree: (display title, HTML file, Doxygen JS file stem)
NAVTREE_ROOT: list[tuple[str, str, str | None]] = [
    ("Root Resource",                    "root_page.html",            "root_page"),
    ("Subscription Service",             "subsrv_main_page.html",     "subsrv_main_page"),
    ("User Service",                     "users_main_page.html",      "users_main_page"),
    ("Controller Service",               "ctrl_main_page.html",       "ctrl_main_page"),
    ("File Service",                     "fs_main_page.html",         "fs_main_page"),
    ("RobotWare Services",               "rwservices_main_page.html", "rwservices_main_page"),
    ("Operations on IO Profinet Device", "ios_device_data_page.html", "ios_device_data_page"),
]

# ============================================================
#  Phase 1 — Crawler via Doxygen .js files
# ============================================================


def parse_js_tree(js_content: str) -> list[tuple[str, str, str | None]]:
    """Parse a Doxygen navtree JavaScript file into a list of navigation entries.

    Each entry in the JS file has the form::

        ["Title", "page.html", "child_js_stem"]

    where the third element is either a JS file stem (string) or ``null``.

    Args:
        js_content: Raw text content of the Doxygen ``.js`` navtree file.

    Returns:
        List of ``(title, html_file, child_js_stem | None)`` tuples.

    Example:
        >>> entries = parse_js_tree('["Get signal", "ios_get_signal.html", null]')
        >>> entries[0]
        ('Get signal', 'ios_get_signal.html', None)
    """
    entries = []
    pattern = re.compile(r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([^\]]+)\]')
    for m in pattern.finditer(js_content):
        title = m.group(1)
        html_ref = m.group(2)
        child = m.group(3).strip()
        child_js = None if child == "null" else child.strip('"')
        entries.append((title, html_ref, child_js))
    return entries


def crawl_js(
    title: str,
    html_file: str,
    child_js_name: str | None,
    breadcrumb: list[str] | None = None,
) -> None:
    """Recursively crawl the Doxygen navtree and populate ``ROUTES``.

    Fetches the ``.js`` file identified by ``child_js_name``, parses its
    entries, and recurses into each child. Leaf nodes (no JS child, empty
    JS, or 404) are appended directly to ``ROUTES``.

    Args:
        title: Display name of the current navigation node.
        html_file: HTML file name associated with this node
            (relative to ``BASE_URL``).
        child_js_name: Doxygen JS file stem for child nodes, or ``None``
            if this node is a leaf.
        breadcrumb: Accumulated breadcrumb path from the root. Defaults
            to an empty list on the first call.
    """
    if breadcrumb is None:
        breadcrumb = []

    current_breadcrumb = breadcrumb + [title]

    if child_js_name is None:
        ROUTES.append({"title": title, "url_suffix": html_file, "breadcrumb": current_breadcrumb})
        log.info("  ✓ [%3d] %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))
        return

    js_url = BASE_URL + child_js_name + ".js"
    if js_url in VISITED_JS:
        return
    VISITED_JS.add(js_url)

    try:
        resp = requests.get(js_url, timeout=10)

        if resp.status_code == 404 or not resp.text.strip():
            ROUTES.append({"title": title, "url_suffix": html_file,
                "breadcrumb": current_breadcrumb})
            log.info("  ✓ [%3d] (no js) %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))
            return

        resp.raise_for_status()
        children = parse_js_tree(resp.text)

        if not children:
            ROUTES.append({"title": title, "url_suffix": html_file,
                "breadcrumb": current_breadcrumb})
            log.info("  ✓ [%3d] (empty js) %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))
            return

        children_htmls = {h for _, h, _ in children}
        if html_file not in children_htmls:
            ROUTES.append({"title": title, "url_suffix": html_file,
                "breadcrumb": current_breadcrumb})
            log.info("  ✓ [%3d] (+ parent) %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))

        log.info("  ⟦☰⟧ /  %s  (%d children)", " > ".join(current_breadcrumb[-3:]), len(children))
        for child_title, child_html, grandchild_js in children:
            crawl_js(child_title, child_html, grandchild_js, current_breadcrumb)
            time.sleep(0.05)

    except Exception as e:
        log.error("  ❌ JS error [%s]: %s", js_url, e)


# ============================================================
#  Phase 2 — Parse each route page
# ============================================================


def extract_section(content: Tag, label: str) -> str:
    """Extract the text content of a named section from a parsed HTML page.

    Searches for a header or label element whose text matches ``label``,
    then collects all sibling text nodes until the next heading.

    Args:
        content: BeautifulSoup tag representing the page content area.
        label: Section label to search for (e.g. ``"URL Params"``).

    Returns:
        Concatenated text content of the section, or an empty string if
        the section is not found.

    Example:
        >>> extract_section(soup_content, "Method")
        'GET'
    """
    header = None
    for tag in content.find_all(True):
        if tag.name in ["h1", "h2", "h3", "h4", "h5", "b", "dt", "strong", "p", "th"] \
                and tag.get_text(strip=True).rstrip(":") == label:
            header = tag
            break
    if not header:
        return ""

    parts = []
    node = header.find_next_sibling()
    while node:
        if node.name in ["h1", "h2", "h3", "h4", "h5"]:
            break
        t = node.get_text(separator="\n", strip=True)
        if t:
            parts.append(t)
        node = node.find_next_sibling()
    return "\n".join(parts)


def parse_route_page(url_suffix: str) -> dict:
    """Fetch and parse a single ABB RWS API documentation page.

    Extracts all structured fields (URL, method, parameters, responses,
    sample calls, notes) from the Doxygen HTML page.

    Args:
        url_suffix: HTML file name relative to ``BASE_URL``
            (e.g. ``"ios_get_signal.html"``).

    Returns:
        Dictionary with keys: ``description``, ``url``, ``method``,
        ``url_params``, ``data_params``, ``success_response``,
        ``error_response``, ``resources``, ``actions``, ``sample_call``,
        ``notes``. On error, returns ``{"error": "<message>"}``.

    Example:
        >>> data = parse_route_page("mastership_request_page.html")
        >>> data["method"]
        'POST'
    """
    try:
        resp = requests.get(BASE_URL + url_suffix, timeout=10)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        content: Tag | None = soup.find("div", class_="contents") or soup.find("body")
        if not content:
            return {}

        data: dict[str, str] = {
            "description": "", "url": "", "method": "",
            "url_params": "", "data_params": "", "success_response": "",
            "error_response": "", "resources": "", "actions": "",
            "sample_call": "", "notes": "",
        }

        h1 = content.find(["h1", "h2"])
        if h1:
            data["description"] = h1.get_text(strip=True)
            nxt = h1.find_next_sibling()
            while nxt and nxt.name not in ["h1", "h2", "h3", "ul", "dl", "table"]:
                t = nxt.get_text(strip=True)
                if t:
                    data["description"] += " — " + t
                    break
                nxt = nxt.find_next_sibling()

        for field, label in [
            ("url",              "URL"),
            ("method",           "Method"),
            ("url_params",       "URL Params"),
            ("data_params",      "Data Params"),
            ("success_response", "Success Response"),
            ("error_response",   "Error Response"),
            ("resources",        "Resources"),
            ("actions",          "Actions"),
            ("sample_call",      "Sample Call"),
            ("notes",            "Notes"),
        ]:
            val = extract_section(content, label)
            if val:
                data[field] = val

        # Fallback: extract URL from raw page text if the section parser missed it
        if not data["url"]:
            full_text = content.get_text()
            m = re.search(r'(/(?:rw|ctrl|user|fileservice|subscription)/[^\s\n<"\']+)', full_text)
            if m:
                data["url"] = m.group(1).strip()

        # Fallback: extract sample call from <pre> blocks containing "curl"
        if not data["sample_call"]:
            for pre in content.find_all("pre"):
                t = pre.get_text(strip=True)
                if "curl" in t.lower():
                    data["sample_call"] = t
                    break

        return data

    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  Phase 3 — JSON + Markdown export
# ============================================================


def export_json(
    full_api: list[dict],
    path: Path = OUTPUT_DIR / "abb_rws_api_full.json",
) -> None:
    """Serialise the full API dataset to a JSON file.

    Args:
        full_api: List of parsed route dictionaries.
        path: Output file path. Defaults to
            ``utils/scraping/abb_rws_api_full.json``.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(full_api, f, ensure_ascii=False, indent=2)
    log.info("   JSON  → %s", path)


def export_markdown(
    full_api: list[dict],
    path: Path = OUTPUT_DIR / "abb_rws_api_full.md",
) -> None:
    """Serialise the full API dataset to a Markdown reference file.

    Each route is rendered as a level-2 heading with all available fields
    formatted as code blocks or inline text.

    Args:
        full_api: List of parsed route dictionaries.
        path: Output file path. Defaults to
            ``utils/scraping/abb_rws_api_full.md``.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write("# ABB Robot Web Services — API Reference\n\n")
        f.write(f"> {len(full_api)} documented routes\n\n---\n\n")
        for route in full_api:
            f.write(f"## {route.get('title', 'N/A')}\n\n")
            bc = route.get("breadcrumb", [])
            if bc:
                f.write(f"**Path:** {' › '.join(bc)}\n\n")
            if route.get("description"):
                f.write(f"{route['description']}\n\n")
            if route.get("url"):
                f.write(f"**URL:** `{route['url']}`  \n")
            if route.get("method"):
                f.write(f"**Method:** `{route['method']}`\n\n")
            for field, label in [
                ("url_params",  "URL Params"),
                ("data_params", "Data Params"),
                ("resources",   "Resources"),
                ("actions",     "Actions"),
            ]:
                if route.get(field):
                    f.write(f"**{label}:**\n```\n{route[field]}\n```\n\n")
            if route.get("success_response"):
                f.write(f"**Success:** {route['success_response']}\n\n")
            if route.get("error_response"):
                f.write(f"**Error:** {route['error_response']}\n\n")
            if route.get("sample_call"):
                f.write(f"**Sample Call:**\n```bash\n{route['sample_call']}\n```\n\n")
            if route.get("notes"):
                f.write(f"**Notes:** {route['notes']}\n\n")
            f.write("---\n\n")
    log.info("    MD    → %s", path)


def build_full_doc() -> None:
    """Orchestrate Phase 2 + Phase 3: parse all routes and export results.

    Loads the route list from ``routes_list.json`` if it exists (skipping
    the crawl), otherwise uses the in-memory ``ROUTES`` list populated by
    ``crawl_js()``. Fetches and parses each route page, then exports the
    full dataset to JSON and Markdown.
    """
    if ROUTES_FILE.exists():
        with open(ROUTES_FILE, encoding="utf-8") as f:
            routes = json.load(f)
        log.info("⟦☰⟧ /  routes_list.json found — %d routes (crawl skipped)\n", len(routes))
    else:
        routes = ROUTES

    full_api = []
    total = len(routes)
    for i, route in enumerate(routes):
        log.info("[%3d/%d]  %s", i + 1, total, route["title"])
        parsed = parse_route_page(route["url_suffix"])
        parsed["title"] = route["title"]
        parsed["breadcrumb"] = route["breadcrumb"]
        parsed["source_url"] = BASE_URL + route["url_suffix"]
        full_api.append(parsed)
        time.sleep(0.12)

    log.info("\n Exporting...")
    export_json(full_api)
    export_markdown(full_api)
    log.info("\n✓ Done — %d routes documented.", len(full_api))


# ============================================================
#  Entry point
# ============================================================

if __name__ == "__main__":
    if ROUTES_FILE.exists():
        log.info("⟦☰⟧ /  routes_list.json found — delete it to force a full re-crawl.\n")
    else:
        log.info("=" * 60)
        log.info("  PHASE 1 — Crawl via Doxygen .js files")
        log.info("=" * 60)

        for title, html_file, child_js in NAVTREE_ROOT:
            crawl_js(title, html_file, child_js)

        log.info("\n%d routes found\n", len(ROUTES))
        with open(ROUTES_FILE, "w", encoding="utf-8") as f:
            json.dump(ROUTES, f, ensure_ascii=False, indent=2)
        log.info(" routes_list.json saved\n")

    log.info("=" * 60)
    log.info("  PHASE 2 — Parsing + Export")
    log.info("=" * 60)
    build_full_doc()
