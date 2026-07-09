import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ============================================================
#  CHEMINS
# ============================================================
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "scrap_raw_output"
OUTPUT_DIR.mkdir(exist_ok=True)

ROUTES_FILE = SCRIPT_DIR / "routes_list.json"
LOG_FILE    = SCRIPT_DIR / "scrape.log"

# ============================================================
#  LOGGER
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
#  CONFIG
# ============================================================
BASE_URL   = "https://developercenter.robotstudio.com/api/rwsApi/"
VISITED_JS: set[str] = set()
ROUTES: list[dict]   = []

NAVTREE_ROOT = [
    ("Root Resource",                    "root_page.html",           "root_page"),
    ("Subscription Service",             "subsrv_main_page.html",    "subsrv_main_page"),
    ("User Service",                     "users_main_page.html",     "users_main_page"),
    ("Controller Service",               "ctrl_main_page.html",      "ctrl_main_page"),
    ("File Service",                     "fs_main_page.html",        "fs_main_page"),
    ("RobotWare Services",               "rwservices_main_page.html","rwservices_main_page"),
    ("Operations on IO Profinet Device", "ios_device_data_page.html","ios_device_data_page"),
]

# ============================================================
#  ÉTAPE 1 — CRAWLER via fichiers .js Doxygen
# ============================================================
def parse_js_tree(js_content: str) -> list[tuple[str, str, str | None]]:
    entries = []
    pattern = re.compile(r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([^\]]+)\]')
    for m in pattern.finditer(js_content):
        title    = m.group(1)
        html_ref = m.group(2)
        child    = m.group(3).strip()
        child_js = None if child == "null" else child.strip('"')
        entries.append((title, html_ref, child_js))
    return entries


def crawl_js(
    title: str,
    html_file: str,
    child_js_name: str | None,
    breadcrumb: list[str] | None = None,
) -> None:
    if breadcrumb is None:
        breadcrumb = []

    current_breadcrumb = breadcrumb + [title]

    if child_js_name is None:
        ROUTES.append({"title": title, "url_suffix": html_file, "breadcrumb": current_breadcrumb})
        log.info("  ✅ [%3d] %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))
        return

    js_url = BASE_URL + child_js_name + ".js"
    if js_url in VISITED_JS:
        return
    VISITED_JS.add(js_url)

    try:
        resp = requests.get(js_url, timeout=10)

        if resp.status_code == 404 or not resp.text.strip():
            ROUTES.append({"title": title, "url_suffix": html_file, "breadcrumb": current_breadcrumb})
            log.info("  ✅ [%3d] (no js) %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))
            return

        resp.raise_for_status()
        children = parse_js_tree(resp.text)

        if not children:
            ROUTES.append({"title": title, "url_suffix": html_file, "breadcrumb": current_breadcrumb})
            log.info("  ✅ [%3d] (empty js) %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))
            return

        children_htmls = {h for _, h, _ in children}
        if html_file not in children_htmls:
            ROUTES.append({"title": title, "url_suffix": html_file, "breadcrumb": current_breadcrumb})
            log.info("  ✅ [%3d] (+ parent) %s", len(ROUTES), " > ".join(current_breadcrumb[-4:]))

        log.info("  📂 %s  (%d enfants)", " > ".join(current_breadcrumb[-3:]), len(children))
        for child_title, child_html, grandchild_js in children:
            crawl_js(child_title, child_html, grandchild_js, current_breadcrumb)
            time.sleep(0.05)

    except Exception as e:
        log.error("  ❌ Erreur JS [%s] : %s", js_url, e)


# ============================================================
#  ÉTAPE 2 — PARSER chaque page de route
# ============================================================
def extract_section(content, label: str) -> str:
    header = None
    for tag in content.find_all(True):
        if tag.name in ["h1","h2","h3","h4","h5","b","dt","strong","p","th"] \
                and tag.get_text(strip=True).rstrip(":") == label:
            header = tag
            break
    if not header:
        return ""

    parts = []
    node = header.find_next_sibling()
    while node:
        if node.name in ["h1","h2","h3","h4","h5"]:
            break
        t = node.get_text(separator="\n", strip=True)
        if t:
            parts.append(t)
        node = node.find_next_sibling()
    return "\n".join(parts)


def parse_route_page(url_suffix: str) -> dict:
    try:
        resp = requests.get(BASE_URL + url_suffix, timeout=10)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        soup    = BeautifulSoup(resp.text, "html.parser")
        content = soup.find("div", class_="contents") or soup.find("body")
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
            while nxt and nxt.name not in ["h1","h2","h3","ul","dl","table"]:
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

        if not data["url"]:
            full_text = content.get_text()
            m = re.search(r'(/(?:rw|ctrl|user|fileservice|subscription)/[^\s\n<"\']+)', full_text)
            if m:
                data["url"] = m.group(1).strip()

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
#  ÉTAPE 3 — EXPORT JSON + MARKDOWN
# ============================================================
def export_json(full_api: list[dict], path: Path = OUTPUT_DIR / "abb_rws_api_full.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(full_api, f, ensure_ascii=False, indent=2)
    log.info("  📄 JSON  → %s", path)


def export_markdown(full_api: list[dict], path: Path = OUTPUT_DIR / "abb_rws_api_full.md") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("# ABB Robot Web Services — API Reference\n\n")
        f.write(f"> {len(full_api)} routes documentées\n\n---\n\n")
        for route in full_api:
            f.write(f"## {route.get('title', 'N/A')}\n\n")
            bc = route.get("breadcrumb", [])
            if bc:
                f.write(f"**Chemin :** {' › '.join(bc)}\n\n")
            if route.get("description"):
                f.write(f"{route['description']}\n\n")
            if route.get("url"):
                f.write(f"**URL :** `{route['url']}`  \n")
            if route.get("method"):
                f.write(f"**Method :** `{route['method']}`\n\n")
            for field, label in [
                ("url_params",       "URL Params"),
                ("data_params",      "Data Params"),
                ("resources",        "Resources"),
                ("actions",          "Actions"),
            ]:
                if route.get(field):
                    f.write(f"**{label} :**\n```\n{route[field]}\n```\n\n")
            if route.get("success_response"):
                f.write(f"**Success :** {route['success_response']}\n\n")
            if route.get("error_response"):
                f.write(f"**Error :** {route['error_response']}\n\n")
            if route.get("sample_call"):
                f.write(f"**Sample Call :**\n```bash\n{route['sample_call']}\n```\n\n")
            if route.get("notes"):
                f.write(f"**Notes :** {route['notes']}\n\n")
            f.write("---\n\n")
    log.info("  📝 MD    → %s", path)


def build_full_doc() -> None:
    if ROUTES_FILE.exists():
        with open(ROUTES_FILE, encoding="utf-8") as f:
            routes = json.load(f)
        log.info("📂 routes_list.json trouvé — %d routes (skip crawl)\n", len(routes))
    else:
        routes = ROUTES

    full_api = []
    total = len(routes)
    for i, route in enumerate(routes):
        log.info("[%3d/%d] ⚙️  %s", i + 1, total, route["title"])
        parsed = parse_route_page(route["url_suffix"])
        parsed["title"]      = route["title"]
        parsed["breadcrumb"] = route["breadcrumb"]
        parsed["source_url"] = BASE_URL + route["url_suffix"]
        full_api.append(parsed)
        time.sleep(0.12)

    log.info("\n💾 Export en cours...")
    export_json(full_api)
    export_markdown(full_api)
    log.info("\n✅ Terminé — %d routes documentées.", len(full_api))


# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    if ROUTES_FILE.exists():
        log.info("📂 routes_list.json trouvé — supprime-le pour relancer le crawl.\n")
    else:
        log.info("=" * 60)
        log.info("  PHASE 1 — Crawl via fichiers .js Doxygen")
        log.info("=" * 60)

        for title, html_file, child_js in NAVTREE_ROOT:
            crawl_js(title, html_file, child_js)

        log.info("\n%d routes trouvées\n", len(ROUTES))
        with open(ROUTES_FILE, "w", encoding="utf-8") as f:
            json.dump(ROUTES, f, ensure_ascii=False, indent=2)
        log.info("💾 routes_list.json sauvegardé\n")

    log.info("=" * 60)
    log.info("  PHASE 2 — Parsing + Export")
    log.info("=" * 60)
    build_full_doc()