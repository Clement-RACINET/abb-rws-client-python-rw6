# Cahier des charges — abb-rws6-python-client

| Champ        | Valeur                                      |
|--------------|---------------------------------------------|
| Version      | 1.0                                         |
| Date         | 2026-07-08                                  |
| Statut       | Référence projet — document vivant          |
| Licence      | MIT (open-source)                           |
| Cible Python | ≥ 3.11                                      |
| Cible RW     | RobotWare 6 exclusivement                   |

---

## 1. Contexte & Objectif

### 1.1 Contexte

ABB RobotWare 6 (RW6) expose une API REST appelée **Robot Web Services
(RWS)** permettant de contrôler un robot industriel via HTTP depuis
n'importe quel client réseau. La documentation officielle recense
**~560 routes** organisées en ~15 domaines fonctionnels couvrant
l'exécution RAPID, les entrées/sorties, le panneau opérateur, la
configuration système, les fichiers, et plus encore.

### 1.2 Objectif

Développer `abb-rws6-python-client`, une **bibliothèque Python moderne,
typée, testée et documentée**, offrant un miroir Python complet et
idiomatique de l'intégralité de l'API RWS ABB RW6.

La bibliothèque est destinée à être publiée sur **PyPI** et utilisée par
des développeurs Python souhaitant intégrer un robot ABB dans leurs
applications sans se soucier des détails HTTP/RWS.

### 1.3 Philosophie directrice

| Principe              | Signification concrète                                         |
|-----------------------|----------------------------------------------------------------|
| **Généricité**        | Aucune valeur métier codée en dur                              |
| **Miroir fidèle**     | 1 module Python = 1 domaine RWS, 1 fonction = 1 endpoint      |
| **Séparation nette**  | API basse (miroir) vs helpers haut niveau (composition)        |
| **Zéro magie**        | Comportement prévisible, erreurs explicites et documentées     |
| **Maintenabilité**    | Code lisible, typé strictement, documenté exhaustivement       |
| **Testabilité**       | 100% de couverture, aucun test nécessitant un robot physique   |

---

## 2. Périmètre fonctionnel

### 2.1 Domaines RWS — Priorités

| Priorité | Domaine RWS         | Package Python          | Statut      |
|----------|---------------------|-------------------------|-------------|
| **P0**   | RAPID / Execution   | `rapid/execution.py`    | ✅ Done     |
| **P0**   | RAPID / Symbol data | `rapid/symbol.py`       | ✅ Done     |
| **P0**   | Mastership          | `mastership.py`         | ✅ Done     |
| **P1**   | Panel               | `panel/`                | 🔜 v0.2     |
| **P1**   | IO System           | `iosystem/`             | 🔜 v0.2     |
| **P1**   | Controller          | `controller/`           | 🔜 v0.2     |
| **P2**   | RAPID / Tasks       | `rapid/tasks.py`        | 📅 v0.3     |
| **P2**   | RAPID / Modules     | `rapid/modules.py`      | 📅 v0.3     |
| **P2**   | File Service        | `fileservice/`          | 📅 v0.3     |
| **P2**   | System Service      | `system/`               | 📅 v0.3     |
| **P3**   | CFG Service         | `cfg/`                  | 📅 v0.4     |
| **P3**   | Elog Service        | `elog/`                 | 📅 v0.4     |
| **P3**   | Motion System       | `motion/`               | 📅 v0.4     |
| **P3**   | User Service        | `user/`                 | 📅 v0.4     |
| **P3**   | Subscription        | `subscription/`         | 📅 v1.1     |
| **P3**   | DIPC Service        | `dipc/`                 | 📅 v1.1     |
| **P4**   | Profinet IO         | `profinet/`             | 📅 v1.2     |
| **P4**   | Vision IV           | `vision/`               | 📅 v1.2     |

### 2.2 Règle de couverture

Les domaines P3 peuvent être **implémentés sans tests complets** à
condition d'être :
- Documentés (docstrings + routes RWS référencées)
- Typés correctement
- Marqués `# status: untested` en en-tête de module

L'objectif final est la couverture des 560 routes.

---

## 3. Architecture

### 3.1 Structure des packages

```
abb_rws_client_python_rw6/
│
├── __init__.py                  ← exports publics (API surface)
├── client.py                    ← clients HTTP (sync + async)
├── exceptions.py                ← hiérarchie complète + codes SYS_CTRL_*
├── serializers.py               ← sérialisation types RAPID ↔ Python
├── mastership.py                ← context manager mastership
├── helpers.py                   ← wrappers haut niveau composés
│
├── rapid/
│   ├── __init__.py
│   ├── execution.py             ← /rw/rapid/execution/*
│   ├── symbol.py                ← /rw/rapid/symbol/* + /rw/rapid/symbol/data/*
│   ├── tasks.py                 ← /rw/rapid/tasks/*
│   ├── modules.py               ← /rw/rapid/modules/*
│   └── ui.py                    ← /rw/rapid/ui/*
│
├── panel/
│   ├── __init__.py
│   ├── controller_state.py      ← /rw/panel/ctrlstate
│   ├── operation_mode.py        ← /rw/panel/opmode
│   └── speed_ratio.py           ← /rw/panel/speedratio
│
├── iosystem/
│   ├── __init__.py
│   ├── signals.py               ← /rw/iosystem/signals/*
│   └── devices.py               ← /rw/iosystem/devices/*
│
├── controller/
│   ├── __init__.py
│   ├── identity.py              ← /rw/identity
│   ├── clock.py                 ← /rw/clock
│   ├── network.py               ← /rw/network
│   └── backup.py                ← /rw/backup
│
├── system/
│   ├── __init__.py
│   └── info.py                  ← /rw/system
│
├── cfg/
│   ├── __init__.py
│   └── domain.py                ← /rw/cfg/*
│
├── elog/
│   ├── __init__.py
│   └── messages.py              ← /rw/elog/*
│
├── motion/
│   ├── __init__.py
│   ├── mechunits.py             ← /rw/motionsystem/mechunits/*
│   └── supervision.py           ← /rw/motionsystem/supervision/*
│
├── user/
│   ├── __init__.py
│   └── grants.py                ← /rw/users/*
│
├── fileservice/
│   ├── __init__.py
│   ├── directory.py             ← /fileservice/directory/*
│   └── file.py                  ← /fileservice/file/*
│
└── subscription/
    ├── __init__.py
    └── websocket.py             ← /subscription/* (WebSocket/long-poll)
```

### 3.2 Couche client — Sync + Async

```
_RWSClientBase          (logique commune : auth, retry, parsing erreurs)
├── RWSClient           → httpx.AsyncClient  (interface async/await)
└── RWSClientSync       → httpx.Client       (interface synchrone)
```

Les deux clients exposent **exactement la même API** :
`get()`, `post()`, `put()`, `delete()` avec les mêmes signatures.
Seule la présence de `async/await` diffère.

Toute la logique de parsing, gestion des erreurs et retry vit dans
`_RWSClientBase` — zéro duplication.

### 3.3 Règle de frontière stricte

| Couche          | Fichier(s)                  | Responsabilité                                      |
|-----------------|-----------------------------|-----------------------------------------------------|
| **Transport**   | `client.py`                 | HTTP, auth Digest/Basic, retry, cookies ABBCX       |
| **Domaine RWS** | `rapid/`, `panel/`, etc.    | 1 fn = 1 endpoint, aucune logique métier            |
| **Sérialisation**| `serializers.py`           | Conversion types Python ↔ format RWS                |
| **Helpers**     | `helpers.py`                | Compose N appels, polling, séquences applicatives   |
| **Exceptions**  | `exceptions.py`             | Hiérarchie complète, codes ABB mappés               |

---

## 4. Gestion des erreurs

### 4.1 Hiérarchie d'exceptions Python

```
RWSError                         ← base de toutes les exceptions RWS
├── RWSConnectionError           ← réseau inaccessible (httpx.ConnectError)
├── RWSTimeoutError              ← timeout réseau ou polling applicatif
├── RWSHTTPError                 ← réponse HTTP inattendue
│   ├── RWSNotFoundError         ← 404 Not Found
│   ├── RWSForbiddenError        ← 403 Forbidden
│   ├── RWSUnauthorizedError     ← 401 Unauthorized
│   └── RWSConflictError         ← 409 Conflict
├── RWSValueError                ← données invalides côté client Python
└── RWSControllerError           ← erreur métier ABB (codes SYS_CTRL_*)
    ├── MastershipDenied         ← SYS_CTRL_E_MASTER_REJECT (-1073445859)
    ├── RWSExecStateError        ← SYS_CTRL_E_EXEC_STATE (-1073442809)
    ├── RWSSymbolNotFound        ← SYS_CTRL_E_NO_SUCH_SYMBOL (-1073442816)
    ├── RWSModeRejectError       ← SYS_CTRL_E_MODE_REJECT (-1073445860)
    └── RWSUASRejectError        ← SYS_CTRL_E_UAS_REJECT (-1073445867)
```

### 4.2 Structure d'une RWSControllerError

Chaque erreur contrôleur expose :

```python
@dataclass
class RWSControllerError(RWSError):
    code: int           # ex: -1073445859
    name: str           # ex: "SYS_CTRL_E_MASTER_REJECT"
    description: str    # ex: "The user does not have required mastership..."
    http_status: int    # code HTTP de la réponse (400, 403, 409...)
```

### 4.3 Les ~150 codes SYS_CTRL_*

Tous les codes sont définis dans `exceptions.py` comme constantes
nommées et intégrés dans un dictionnaire de lookup :

```python
CTRL_CODES: dict[int, tuple[str, str]] = {
    -1073445859: ("SYS_CTRL_E_MASTER_REJECT",
                  "The user does not have required mastership..."),
    ...
}
```

Le parsing des réponses d'erreur RWS dans `client.py` utilise ce
dictionnaire pour lever l'exception la plus spécifique possible.

---

## 5. Authentification

| Méthode      | Statut      | Notes                                              |
|--------------|-------------|----------------------------------------------------|
| Digest Auth  | ✅ Standard  | Obligatoire RW6, implémenté via `httpx`            |
| Basic Auth   | ⚙️ Optionnel | Désactivé par défaut sur le contrôleur, configurable |
| Cookie ABBCX | ✅ Géré      | Session UAS maintenue automatiquement              |
| Token/OAuth  | ❌ Non supporté | Non disponible sur RW6                          |

---

## 6. Standards techniques

| Critère           | Choix                                          |
|-------------------|------------------------------------------------|
| Python            | ≥ 3.11                                         |
| HTTP client       | `httpx` (sync + async, même paquet)            |
| Typage            | PEP 604 (`X \| Y`), `mypy --strict`            |
| Linting           | `ruff`                                         |
| Tests             | `pytest` + `pytest-asyncio`, coverage 100% P0/P1 |
| Gestion deps      | `pixi`                                         |
| Versioning        | SemVer (`MAJOR.MINOR.PATCH`)                   |
| Documentation     | Docstrings Google style + MkDocs + mkdocstrings |
| CI/CD             | GitLab CI (lint → test → coverage → docs)      |
| Publication       | PyPI via `hatch` ou `flit`                     |

---

## 7. Conventions de développement

### 7.1 Nommage

| Élément              | Convention                  | Exemple                        |
|----------------------|-----------------------------|--------------------------------|
| Fonctions publiques  | `verbe_nom()`               | `get_execution_state()`        |
| Dataclasses résultat | `NomDomaine` + suffixe      | `ExecutionState`, `SignalInfo` |
| Constantes routes    | `_NOM_PATH` (privées)       | `_EXECUTION_BASE`              |
| Types Literal ABB    | `NomMode`                   | `StopMode`, `CycleMode`        |
| Packages domaine     | Nom RWS en minuscule        | `rapid/`, `iosystem/`          |

### 7.2 Documentation obligatoire par fonction publique

```python
async def nom_fonction(client: RWSClient, ...) -> ReturnType:
    """Résumé en une ligne.

    Description plus longue si nécessaire.

    Route : METHOD /chemin/rws/exact

    Contraintes ABB :
        - Mastership requis / non requis
        - Mode opératoire (auto/manuel)
        - Toute contrainte spécifique RW6

    Args:
        client: Instance RWSClient ouverte.
        param1: Description + valeurs acceptées.

    Returns:
        Description du type retourné.

    Raises:
        RWSControllerError: Si le contrôleur rejette l'opération.
        RWSHTTPError: Réponse HTTP inattendue.
        RWSConnectionError: Réseau inaccessible.

    Example:
        ::

            result = await nom_fonction(client, param1="valeur")
    """
```

### 7.3 En-tête de module

```python
# abb_rws_client/rapid/execution.py
"""
Contrôle de l'exécution RAPID — /rw/rapid/execution/*

Routes couvertes :
    GET  /rw/rapid/execution              → état d'exécution
    POST /rw/rapid/execution/start        → démarrer
    POST /rw/rapid/execution/stop         → arrêter
    POST /rw/rapid/execution/resetpp      → reset PP

Référence ABB : RobotWare 6 RWS API — RAPID Service
Status        : tested (coverage 100%)
"""
```

### 7.4 Tests

- Mock HTTP via `httpx.AsyncBaseTransport` pour les modules domaine
- Mock fonctions via `unittest.mock.AsyncMock` pour les helpers
- Couverture **100%** obligatoire pour P0 et P1
- Couverture **best-effort** pour P2/P3 (marqués `# status: untested`)
- Aucun test ne doit nécessiter un contrôleur physique

---

## 8. Documentation (MkDocs)

### 8.1 Structure docs/

```
docs/
├── index.md                 ← présentation, installation, quickstart
├── authentication.md        ← Digest Auth, Basic Auth, cookies
├── error_handling.md        ← hiérarchie exceptions, codes SYS_CTRL_*
├── async_sync.md            ← RWSClient vs RWSClientSync
├── api/
│   ├── rapid.md             ← référence auto-générée depuis docstrings
│   ├── panel.md
│   ├── iosystem.md
│   └── ...
└── guides/
    ├── quickstart.md        ← exemple complet en 10 lignes
    ├── mastership.md        ← usage du context manager
    └── helpers.md           ← wrappers haut niveau
```

### 8.2 Génération automatique

`mkdocstrings` génère la référence API directement depuis les docstrings.
Toute fonction documentée selon §7.2 apparaît automatiquement dans
`docs/api/`.

---

## 9. Roadmap

### v0.1 — Infrastructure & RAPID core (en cours)
- [x] `client.py` — session HTTP async, Digest Auth, retry, cookies
- [x] `exceptions.py` — hiérarchie de base
- [x] `mastership.py` — context manager
- [x] `serializers.py` — types RAPID
- [x] `rapid/execution.py` — 4 endpoints
- [x] `rapid/symbol.py` — get/set variables RAPID
- [x] `helpers.py` — reset_and_start, wait_until_stopped, wait_for_var
- [ ] Refactor structure → packages `rapid/`, etc.
- [ ] `exceptions.py` enrichi — tous les codes `SYS_CTRL_*`
- [ ] `client.py` enrichi — sync + async, Basic Auth optionnel
- [ ] `__init__.py` — exports publics propres
- [ ] `README.md` + `SPEC.md`
- [ ] CI GitLab (lint + test + coverage)

### v0.2 — Panel, IO, Controller
- [ ] `panel/` — controller_state, operation_mode, speed_ratio
- [ ] `iosystem/` — signals, devices
- [ ] `controller/` — identity, clock, backup
- [ ] MkDocs configuré et déployé

### v0.3 — RAPID étendu + Fichiers + System
- [ ] `rapid/tasks.py`, `rapid/modules.py`
- [ ] `fileservice/`
- [ ] `system/`

### v0.4 — CFG, Elog, Motion, User
- [ ] `cfg/`, `elog/`, `motion/`, `user/`

### v1.0 — Publication PyPI
- [ ] Couverture complète P0→P3
- [ ] Documentation complète déployée
- [ ] Publication PyPI

### v1.1 — Subscription (WebSocket/long-poll)
- [ ] `subscription/` — événements temps réel

---

## 10. Prochaines actions immédiates (v0.1)

Dans cet ordre strict :

1. **Refactor `exceptions.py`** — intégrer les ~150 codes `SYS_CTRL_*`
   et enrichir la hiérarchie
2. **Refactor `client.py`** — ajouter `RWSClientSync`, Basic Auth optionnel,
   mapping HTTP → exceptions enrichies
3. **Refactor structure** — déplacer `rapid_variable.py` → `rapid/symbol.py`,
   `execution.py` → `rapid/execution.py`
4. **`__init__.py`** — exports publics
5. **`SPEC.md`** — committer ce document dans le repo
6. **CI GitLab** — pipeline lint + test + coverage
7. **MkDocs** — configuration de base
```