# CONTEXT.md — Fichier de contexte IA pour abb-rws6-python-client

> Ce fichier est le document de référence unique destiné à être fourni
> comme contexte à tout assistant IA travaillant sur ce projet.
> Il décrit sans ambiguïté le projet, ses contraintes, son architecture
> et ses conventions. Aucune supposition ne doit être faite au-delà de
> ce qui est écrit ici.

---

## 0. Accès au code source

Le code source du projet est hébergé sur GitLab et doit être consulté
systématiquement pour connaître l'état réel du code avant toute
génération ou modification.

| Champ                 | Valeur                                              |
| --------------------- | --------------------------------------------------- |
| URL                   | https://gitlab.ensam.eu/lcfc/abb-rws-client-python-rw6 |
| Nom du repo           | `abb-rws6-python-client`                          |
| Nom du package Python | `abb_rws_client`                                  |
| Branche principale    | `main`                                            |
| Visibilité           | Public                                              |

Avant de générer du code, l'IA doit accéder au repo pour lire les
fichiers existants et ne jamais supposer leur contenu.

---

## 1. Description du projet

`abb-rws6-python-client` est une bibliothèque Python open-source
(licence MIT) qui implémente un **miroir Python complet et 1:1** de
l'API REST **Robot Web Services (RWS)** exposée par les contrôleurs
ABB équipés de **RobotWare 6 (RW6) exclusivement**.

L'API RWS ABB RW6 recense environ 560 routes HTTP organisées en
domaines fonctionnels (RAPID, IO, Panel, Controller, CFG, Elog,
Motion, File, System, User, Subscription, DIPC, Profinet, Vision).

La bibliothèque est destinée à être publiée sur **PyPI** et utilisée
par des développeurs Python intégrant un robot ABB dans leurs
applications.

---

## 2. Contraintes absolues — à respecter sans exception

1. **Miroir 1:1 strict** : chaque route RWS ABB a exactement une
   fonction Python correspondante dans le package `rws/`. La structure
   des dossiers Python reflète l'arborescence des routes RWS.
   Aucun regroupement arbitraire n'est autorisé dans `rws/`.
2. **Aucune valeur métier codée en dur** : aucune constante applicative
   (nom de module RAPID, nom de tâche, valeur de variable) ne doit
   apparaître dans `rws/`. Les paramètres sont toujours explicites.
3. **Séparation stricte rws/ vs highlevel/** :

   - `rws/` : fonctions atomiques, 1 fonction = 1 endpoint HTTP.
     Aucune logique composée, aucun polling, aucun appel à une autre
     fonction du package.
   - `highlevel/` : fonctions composées qui appellent plusieurs
     fonctions de `rws/`. Aucun appel HTTP direct.
4. **RobotWare 6 uniquement** : aucune compatibilité RW7/OmniCore
   n'est dans le scope de ce projet.
5. **Zéro test nécessitant un robot physique** : tous les tests
   utilisent des transports HTTP mockés (`httpx.AsyncBaseTransport`)
   ou des mocks de fonctions (`unittest.mock.AsyncMock`).
6. **Typage strict** : syntaxe PEP 604 (`X | Y`) pour toutes les
   unions de types. Compatible Python ≥ 3.11. `mypy --strict` doit
   passer sans erreur.
7. **Couverture 100%** pour tous les modules P0 et P1. Les modules
   P2/P3 sont marqués `# status: untested` en en-tête et exemptés.
8. **Documentation exhaustive** : chaque fonction publique respecte
   le template de docstring défini en §7 de ce document.

---

## 3. Architecture du package

### 3.1 Structure des dossiers

```
abb_rws_client/
│
├── __init__.py                  ← exports publics (surface API)
│
├── _core/                       ← infrastructure interne
│   ├── __init__.py
│   ├── client.py                ← RWSClient (async) + RWSClientSync (sync)
│   ├── exceptions.py            ← hiérarchie complète + codes SYS_CTRL_*
│   └── serializers.py           ← sérialisation types RAPID ↔ Python
│
├── rws/                         ← miroir 1:1 de l'API RWS ABB RW6
│   ├── __init__.py
│   │
│   ├── rapid/
│   │   ├── __init__.py
│   │   ├── execution.py         ← /rw/rapid/execution/*
│   │   ├── symbol/
│   │   │   ├── __init__.py
│   │   │   ├── data.py          ← /rw/rapid/symbol/data/*
│   │   │   └── properties.py    ← /rw/rapid/symbol/properties/*
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── task.py          ← /rw/rapid/tasks/{task}/*
│   │   │   ├── motion.py        ← /rw/rapid/tasks/{task}/motion/*
│   │   │   └── program.py       ← /rw/rapid/tasks/{task}/program/*
│   │   └── modules/
│   │       ├── __init__.py
│   │       └── module.py        ← /rw/rapid/modules/{module}/*
│   │
│   ├── panel/
│   │   ├── __init__.py
│   │   ├── ctrlstate.py         ← /rw/panel/ctrlstate
│   │   ├── opmode.py            ← /rw/panel/opmode
│   │   └── speedratio.py        ← /rw/panel/speedratio
│   │
│   ├── iosystem/
│   │   ├── __init__.py
│   │   ├── signals.py           ← /rw/iosystem/signals/*
│   │   ├── devices.py           ← /rw/iosystem/devices/*
│   │   └── networks.py          ← /rw/iosystem/networks/*
│   │
│   ├── mastership/
│   │   ├── __init__.py
│   │   └── mastership.py        ← /rw/mastership/*
│   │
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── identity.py          ← /rw/identity
│   │   ├── clock.py             ← /rw/clock
│   │   ├── network.py           ← /rw/network
│   │   └── backup.py            ← /rw/backup
│   │
│   ├── system/
│   │   ├── __init__.py
│   │   └── info.py              ← /rw/system
│   │
│   ├── cfg/
│   │   ├── __init__.py
│   │   └── domain.py            ← /rw/cfg/*
│   │
│   ├── elog/
│   │   ├── __init__.py
│   │   └── messages.py          ← /rw/elog/*
│   │
│   ├── motion/
│   │   ├── __init__.py
│   │   ├── mechunits.py         ← /rw/motionsystem/mechunits/*
│   │   └── supervision.py       ← /rw/motionsystem/supervision/*
│   │
│   ├── user/
│   │   ├── __init__.py
│   │   └── grants.py            ← /rw/users/*
│   │
│   ├── fileservice/
│   │   ├── __init__.py
│   │   ├── directory.py         ← /fileservice/directory/*
│   │   └── file.py              ← /fileservice/file/*
│   │
│   ├── dipc/
│   │   ├── __init__.py
│   │   └── queue.py             ← /rw/dipc/*
│   │
│   ├── subscription/
│   │   ├── __init__.py
│   │   └── websocket.py         ← /subscription/* (WebSocket/long-poll)
│   │
│   ├── profinet/
│   │   ├── __init__.py
│   │   └── devices.py           ← /rw/profinet/*
│   │
│   └── vision/
│       ├── __init__.py
│       └── cameras.py           ← /rw/vision/*
│
├── highlevel/                   ← wrappers composés (aucun endpoint direct)
│   ├── __init__.py
│   ├── execution.py             ← reset_and_start, wait_until_stopped
│   ├── variables.py             ← wait_for_var, bulk read/write
│   └── io.py                    ← set_signal, wait_for_signal
│
└── tests/
    ├── rws/
    │   ├── rapid/
    │   │   ├── test_execution.py
    │   │   └── test_symbol_data.py
    │   ├── panel/
    │   └── iosystem/
    └── highlevel/
        └── test_execution.py
```

### 3.2 Couche client — Sync et Async

La logique commune (authentification, retry, parsing des erreurs,
gestion des cookies) est centralisée dans `_RWSClientBase`.
Deux clients concrets en héritent :

```
_RWSClientBase          ← logique commune : auth, retry, erreurs, cookies
├── RWSClient           → httpx.AsyncClient  (interface async/await)
└── RWSClientSync       → httpx.Client       (interface synchrone)
```

Les deux clients exposent exactement les mêmes méthodes :
`get()`, `post()`, `put()`, `delete()`.
La seule différence est la présence ou l'absence de `async/await`.
Aucune logique métier ne doit être dupliquée entre les deux.

### 3.3 Règle de frontière stricte

| Couche         | Emplacement              | Responsabilité exclusive                         |
| -------------- | ------------------------ | ------------------------------------------------- |
| Transport      | `_core/client.py`      | HTTP, auth, retry, cookies ABBCX                  |
| Miroir RWS     | `rws/**`               | 1 fonction = 1 endpoint, aucune logique composée |
| Sérialisation | `_core/serializers.py` | Conversion types Python ↔ format RWS             |
| Wrappers       | `highlevel/**`         | Composition de fonctions`rws/`, polling         |
| Exceptions     | `_core/exceptions.py`  | Hiérarchie complète, tous les codes SYS_CTRL_*  |

---

## 4. Authentification

L'authentification sur RobotWare 6 fonctionne comme suit :

- **Digest Auth** : méthode obligatoire et primaire. Le contrôleur
  retourne HTTP 401 sur toute requête non authentifiée et exige un
  handshake Digest. Implémenté via `httpx.DigestAuth`.
- **Cookie ABBCX** : après authentification Digest réussie, le
  contrôleur retourne un cookie de session `ABBCX` qui maintient la
  session UAS (User Authorization System) active. Ce cookie doit être
  renvoyé sur toutes les requêtes suivantes. Géré automatiquement par
  `_RWSClientBase`.
- **Basic Auth** : techniquement supporté par le serveur AppWeb intégré
  au contrôleur, mais désactivé par défaut dans les configurations de
  sécurité standard. Disponible comme option configurable dans
  `_RWSClientBase`, non activé par défaut.
- **Token / OAuth** : non supporté par RobotWare 6. Hors scope.

---

## 5. Gestion des erreurs

### 5.1 Hiérarchie d'exceptions

```
RWSError                         ← classe de base
├── RWSConnectionError           ← réseau inaccessible
├── RWSTimeoutError              ← timeout réseau ou polling
├── RWSHTTPError                 ← réponse HTTP inattendue
│   ├── RWSUnauthorizedError     ← 401
│   ├── RWSForbiddenError        ← 403
│   ├── RWSNotFoundError         ← 404
│   └── RWSConflictError         ← 409
├── RWSValueError                ← données invalides côté client Python
└── RWSControllerError           ← erreur métier ABB (codes SYS_CTRL_*)
    ├── MastershipDenied         ← SYS_CTRL_E_MASTER_REJECT (-1073445859)
    ├── RWSExecStateError        ← SYS_CTRL_E_EXEC_STATE (-1073442809)
    ├── RWSSymbolNotFound        ← SYS_CTRL_E_NO_SUCH_SYMBOL (-1073442816)
    ├── RWSModeRejectError       ← SYS_CTRL_E_MODE_REJECT (-1073445860)
    └── RWSUASRejectError        ← SYS_CTRL_E_UAS_REJECT (-1073445867)
```

### 5.2 Structure de RWSControllerError

```python
@dataclass
class RWSControllerError(RWSError):
    code: int           # ex : -1073445859
    name: str           # ex : "SYS_CTRL_E_MASTER_REJECT"
    description: str    # ex : "The user does not have required mastership..."
    http_status: int    # code HTTP de la réponse (400, 403, 409...)
```

### 5.3 Dictionnaire des codes SYS_CTRL_*

Tous les codes retour ABB sont définis dans `_core/exceptions.py`
dans un dictionnaire de lookup `CTRL_CODES` :

```python
CTRL_CODES: dict[int, tuple[str, str]] = {
    code_entier: ("NOM_SYMBOLIQUE", "Description humaine"),
    ...
}
```

Le fichier de référence complet des codes (`return_codes.html` ou
équivalent) est fourni séparément comme fichier de contexte.
`_core/client.py` utilise ce dictionnaire pour lever l'exception
la plus spécifique possible lors du parsing des réponses d'erreur.

---

## 6. Standards techniques

| Critère         | Valeur retenue                                  |
| ---------------- | ----------------------------------------------- |
| Python           | ≥ 3.11                                         |
| HTTP client      | `httpx` (sync + async dans le même paquet)   |
| Typage           | PEP 604 (`X \| Y`), `mypy --strict`          |
| Linting          | `ruff`                                        |
| Tests            | `pytest` + `pytest-asyncio`                 |
| Couverture       | `pytest-cov`, 100% obligatoire P0/P1          |
| Gestion des deps | `pixi`                                        |
| Versioning       | SemVer (`MAJOR.MINOR.PATCH`)                  |
| Documentation    | Docstrings Google style + MkDocs + mkdocstrings |
| CI/CD            | GitLab CI (lint → test → coverage → docs)    |
| Publication      | PyPI                                            |

---

## 7. Conventions de code

### 7.1 Nommage

| Élément             | Convention               | Exemple                            |
| --------------------- | ------------------------ | ---------------------------------- |
| Fonctions publiques   | `verbe_nom()`          | `get_execution_state()`          |
| Dataclasses résultat | `NomDomaine` + suffixe | `ExecutionState`, `SignalInfo` |
| Constantes de routes  | `_NOM_PATH` (privées) | `_EXECUTION_BASE`                |
| Types Literal ABB     | `NomMode`              | `StopMode`, `CycleMode`        |
| Packages domaine      | Nom RWS en minuscule     | `rapid/`, `iosystem/`          |

### 7.2 Template de docstring obligatoire

Toute fonction publique dans `rws/` ou `highlevel/` doit respecter
ce template sans exception :

```python
async def nom_fonction(client: RWSClient, ...) -> ReturnType:
    """Résumé en une ligne.

    Description étendue si nécessaire.

    Route : METHOD /chemin/rws/exact

    Contraintes ABB :
        - Mastership requis / non requis
        - Mode opératoire requis (auto / manuel / indifférent)
        - Toute autre contrainte spécifique RW6

    Args:
        client: Instance RWSClient ou RWSClientSync ouverte.
        param1: Description et valeurs acceptées.

    Returns:
        Description précise du type retourné.

    Raises:
        RWSControllerError: Le contrôleur a retourné un code SYS_CTRL_*.
        RWSHTTPError: Réponse HTTP inattendue.
        RWSConnectionError: Réseau inaccessible.
        RWSTimeoutError: Timeout dépassé (fonctions highlevel/ uniquement).

    Example:
        ::

            result = await nom_fonction(client, param1="valeur")
    """
```

### 7.3 Template d'en-tête de module

```python
# abb_rws_client/rws/rapid/execution.py
"""
Contrôle de l'exécution RAPID.

Miroir de : /rw/rapid/execution/*
Référence : ABB RobotWare 6 — Robot Web Services API — RAPID Service

Routes couvertes :
    GET  /rw/rapid/execution              → état d'exécution complet
    POST /rw/rapid/execution/start        → démarrer l'exécution
    POST /rw/rapid/execution/stop         → arrêter l'exécution
    POST /rw/rapid/execution/resetpp      → reset program pointer

Status  : tested
Coverage: 100%
"""
```

Pour les modules non encore testés :

```python
# Status  : untested
# Coverage: N/A
```

### 7.4 Règles de tests

- Les tests des modules `rws/` utilisent exclusivement des transports
  HTTP mockés via `httpx.AsyncBaseTransport`. Aucun appel réseau réel.
- Les tests des modules `highlevel/` mockent les fonctions `rws/` via
  `unittest.mock.AsyncMock`. Aucun appel HTTP direct.
- Chaque test vérifie : la route appelée, la méthode HTTP, le payload
  envoyé, et le type de retour.
- La couverture 100% est obligatoire pour P0 et P1.
- Les modules P2/P3 marqués `# Status: untested` sont exclus de
  l'obligation de couverture.

---

## 8. Documentation MkDocs

### 8.1 Structure docs/

```
docs/
├── index.md
├── authentication.md
├── error_handling.md
├── async_sync.md
├── api/
│   ├── rapid.md
│   ├── panel.md
│   ├── iosystem.md
│   └── ...
└── guides/
    ├── quickstart.md
    ├── mastership.md
    └── highlevel.md
```

### 8.2 Génération automatique

`mkdocstrings` génère la référence API directement depuis les
docstrings. Toute fonction respectant le template §7.2 est
automatiquement incluse dans `docs/api/`.

---

## 9. Fichiers de contexte complémentaires

Les fichiers suivants sont fournis séparément et font partie intégrante
du contexte de ce projet. L'IA doit les utiliser comme référence
autoritaire :

| Fichier               | Contenu                                        |
| --------------------- | ---------------------------------------------- |
| `return_codes.html` | Les ~150 codes SYS_CTRL_* ABB avec nom, code   |
|                       | entier et description                          |
| `routes_tree.txt`   | Arborescence complète des ~560 routes RWS ABB |
|                       | organisées hiérarchiquement                  |

Ces fichiers définissent la **vérité de référence** pour :

- La structure des dossiers dans `rws/`
- Le contenu du dictionnaire `CTRL_CODES` dans `_core/exceptions.py`
- La liste exhaustive des fonctions à implémenter

Toute décision d'architecture dans `rws/` doit être justifiable
par une entrée dans `routes_tree.txt`. Toute exception dans
`_core/exceptions.py` doit être justifiable par une entrée dans
`return_codes.html`.

---

## 10. Instructions

1. **Consulter le repo** (`https://gitlab.ensam.eu/lcfc/abb-rws-client-python-rw6`)
   avant toute génération de code pour connaître l'état réel des
   fichiers existants.
2. **Ne jamais supposer** la structure ou le contenu d'un fichier
   non consulté.
3. **Respecter les contraintes absolues** du §2 sans exception ni
   compromis.
4. **Générer du code complet** : aucun placeholder, aucun `# TODO`,
   aucun `pass` dans le code fonctionnel. Les fonctions non encore
   implémentées sont absentes du fichier, pas présentes avec un corps
   vide.
5. **Générer les tests en même temps que le code** : tout module
   P0/P1 livré sans ses tests est considéré incomplet.
6. **Respecter le template de docstring** §7.2 pour chaque fonction
   publique sans exception.
7. **Ne pas modifier `_core/`** sans instruction explicite : ces
   fichiers sont la fondation partagée par tous les modules.
8. **Utiliser les fichiers de contexte complémentaires** (§9) comme
   référence autoritaire pour les routes et les codes d'erreur.
   En l'absence de ces fichiers dans le contexte de la session,
   demander explicitement à l'utilisateur de les fournir avant de
   générer du code dépendant de leur contenu.
