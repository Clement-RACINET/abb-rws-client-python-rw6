
# `contrib/` — Internal development tools

This directory contains the tools used to **build and maintain**
the `abb_rws_client` library. It is **not** part of the published package
(excluded via `pyproject.toml → [tool.hatch.build.targets.wheel]`).

---

## Structure

```

contrib/
├── docs/
│   ├── config.py          # Centralised MkDocs pipeline configuration
│   ├── generate_api.py    # Markdown page generator + mkdocs.yml injection
│   ├── hooks.py           # MkDocs post-build hook (copies htmlcov/)
│   └── run_docs.py        # Pipeline orchestrator (API + coverage + serve)
├── generator/
│   └── main.py            # Source code generator for rws/ and tests/rws/
├── scraping/
│   ├── scrape.py                        # ABB Developer Center scraper
│   ├── abb_rws_api_full.json            # Source of truth: 542 ABB RWS6 endpoints
│   ├── abb_rws_api_full.md              # Human-readable version of the JSON
│   ├── architecture_api.txt             # Tree view of the ABB API
│   ├── routes_list.json                 # Raw route list (crawl cache)
│   ├── robot_controller_return_code.txt # ABB return codes reference
│   └── scrape.log                       # Log of the last scraping run
└── export_structure.py    # Exports the repository tree to a .txt file

```

---

## Workflow

### 1. Scraping *(rare — only if the ABB API changes)*

```bash
pixi run python contrib/scraping/scrape.py
```

Produces `abb_rws_api_full.json` by scraping the ABB Developer Center.
**Do not run without a reason** — the ABB website may block repeated requests.

### 2. Code generation *(after modifying the JSON or the generator)*

```bash
# Delete existing generated files
rm -rf abb_rws_client/rws tests/rws          # Linux / macOS
rmdir /s /q abb_rws_client\rws tests\rws     # Windows

# Regenerate everything
pixi run python contrib/generator/main.py

# Verify
pixi run python -m pytest tests/ -v
```

Available options:

| Option              | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `--dry-run`       | Show what would be generated without writing any file   |
| `--only <module>` | Generate a single module only (e.g.`rapid/execution`) |

### 3. Documentation *(after modifying docstrings or the API)*

```bash
pixi run python contrib/docs/run_docs.py
```

Generates API Markdown pages, produces the coverage report, and starts
`mkdocs serve`.

---

## Generator architecture (`generator/main.py`)

The generator reads `abb_rws_api_full.json` and produces:

- **`abb_rws_client/rws/**/*.py`** — atomic functions, 1 function = 1 HTTP endpoint
- **`tests/rws/**/*.py`** — unit tests with `httpx.AsyncBaseTransport` mocks

### Routing principle

Each ABB endpoint has a `breadcrumb`
(e.g. `["Controller Service", "Operations on Clock Resource", "Get timezone actions"]`).
The `_ROUTING_TABLE` maps these breadcrumbs to Python module paths:

```
["Controller Service", "Operations on Clock Resource", ...]
    → rws/ctrl/clock.py
    → tests/rws/ctrl/test_clock.py
```

### Special case: URLs with a fixed query string

Some ABB URLs contain a query string in the `url` field itself
(e.g. `/ctrl/clock/timezone?action=show`). The generator handles these correctly:

- The path and query string are **split before code generation**
- Fixed params (`action=show`) are injected into `params={...}` in the generated code
- They are **not** exposed as Python function arguments
- Tests verify `url.path` and `url.params["action"]` separately

---

## Rules

1. **Never edit `abb_rws_client/rws/` manually** — it will be overwritten on the next generation run.
2. **Never edit `tests/rws/` manually** — same reason.
3. Business logic belongs in `abb_rws_client/highlevel/`.
4. Routing fixes belong in `_ROUTING_TABLE` inside `main.py`.
5. Parsing fixes belong in `parse_query_params()` or `parse_body_params()` inside `main.py`.
