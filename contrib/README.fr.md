## `contrib/README.fr.md` (FR)

```markdown
# `contrib/` — Outils de développement interne

Ce dossier contient les outils utilisés pour **construire et maintenir**
la bibliothèque `abb_rws_client`. Il ne fait **pas** partie du package
publié (exclu via `pyproject.toml → [tool.hatch.build.targets.wheel]`).

---

## Structure
```

contrib/
├── docs/
│   ├── config.py          # Configuration centralisée de la pipeline MkDocs
│   ├── generate_api.py    # Générateur de pages Markdown + injection mkdocs.yml
│   ├── hooks.py           # Hook MkDocs post-build (copie htmlcov/)
│   └── run_docs.py        # Orchestrateur de la pipeline (API + coverage + serve)
├── generator/
│   └── main.py            # Générateur de code source rws/ et tests/rws/
├── scraping/
│   ├── scrape.py                        # Scraper du Developer Center ABB
│   ├── abb_rws_api_full.json            # Source de vérité : 542 endpoints ABB RWS6
│   ├── abb_rws_api_full.md              # Version lisible du JSON
│   ├── architecture_api.txt             # Vue arborescente de l'API ABB
│   ├── routes_list.json                 # Liste brute des routes (cache du crawl)
│   ├── robot_controller_return_code.txt # Référence des codes retour ABB
│   └── scrape.log                       # Journal du dernier scraping
├── export_structure.py    # Exporte la structure du repo dans un fichier .txt
└── fix_init.py            # Audite et réécrit tous les fichiers __init__.py

```

---

## Workflow

### 1. Scraping *(rare — uniquement si l'API ABB évolue)*

```bash
pixi run python contrib/scraping/scrape.py
```

Produit `abb_rws_api_full.json` en scrapant le Developer Center ABB.
**Ne pas lancer sans raison** — le site ABB peut bloquer les requêtes répétées.

### 2. Génération du code *(après modification du JSON ou du générateur)*

```bash
# Supprimer les fichiers générés existants
rm -rf abb_rws_client/rws tests/rws          # Linux / macOS
rmdir /s /q abb_rws_client\rws tests\rws     # Windows

# Régénérer tout
pixi run python contrib/generator/main.py

# Vérifier
pixi run python -m pytest tests/ -v
```

Options disponibles :

| Option              | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `--dry-run`       | Affiche ce qui serait généré sans écrire de fichier |
| `--only <module>` | Ne génère qu'un module (ex :`rapid/execution`)      |

### 3. Documentation *(après modification des docstrings ou de l'API)*

```bash
pixi run python contrib/docs/run_docs.py
```

Génère les pages Markdown de l'API, produit le rapport de coverage et lance
`mkdocs serve`.

---

## Architecture du générateur (`generator/main.py`)

Le générateur lit `abb_rws_api_full.json` et produit :

- **`abb_rws_client/rws/**/*.py`** — fonctions atomiques, 1 fonction = 1 endpoint HTTP
- **`tests/rws/**/*.py`** — tests unitaires avec mock `httpx.AsyncBaseTransport`

### Principe de routage

Chaque endpoint ABB possède un `breadcrumb`
(ex : `["Controller Service", "Operations on Clock Resource", "Get timezone actions"]`).
La `_ROUTING_TABLE` mappe ces breadcrumbs vers des chemins de modules Python :

```
["Controller Service", "Operations on Clock Resource", ...]
    → rws/ctrl/clock.py
    → tests/rws/ctrl/test_clock.py
```

### Cas particulier : URLs avec query string fixe

Certaines URLs ABB contiennent un query string dans le champ `url` lui-même
(ex : `/ctrl/clock/timezone?action=show`). Le générateur les traite correctement :

- Le path et le query string sont **séparés avant génération**
- Les params fixes (`action=show`) sont injectés dans `params={...}` côté code
- Ils ne sont **pas** exposés comme arguments de la fonction Python
- Les tests vérifient `url.path` et `url.params["action"]` séparément

---

## Règles

1. **Ne jamais modifier `abb_rws_client/rws/` manuellement** — tout sera écrasé à la prochaine génération.
2. **Ne jamais modifier `tests/rws/` manuellement** — idem.
3. La logique métier va dans `abb_rws_client/highlevel/`.
4. Les corrections de mapping vont dans `_ROUTING_TABLE` de `main.py`.
5. Les corrections de parsing vont dans `parse_query_params()` ou `parse_body_params()` de `main.py`.
