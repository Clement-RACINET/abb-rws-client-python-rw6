# abb_rws_client_python_rw6

Client Python asynchrone pour les contrôleurs de robots ABB via l'API
[Robot Web Services (RWS)](https://developercenter.robotstudio.com/api/rwsApi/)
sous **RobotWare 6**.

> **RobotWare 7 / OmniCore est hors périmètre.**

---

## Fonctionnalités

| Domaine              | Opérations                                                                        |
| -------------------- | --------------------------------------------------------------------------------- |
| Session              | Authentification HTTP Digest, cookie ABBCX, nouvelle tentative automatique        |
| Mastership RAPID     | Acquisition / libération (gestionnaire de contexte `async with`)                  |
| Variables RAPID      | `get` / `set` — `num`, `bool`, `string`, `array`, `robtarget`                     |
| Exécution RAPID      | Lecture / contrôle de l'état d'exécution (`running` / `stopped`)                  |
| Signaux IO           | Lecture / écriture de signaux numériques et analogiques                           |
| Contrôleur           | Panneau, système de mouvement, CFG, elog, service de fichiers, abonnements        |
| Couverture           | 710 tests unitaires — 99% de couverture — `ruff` clean                            |

---

## Prérequis

- [pixi](https://pixi.sh) ≥ 0.20
- Python 3.11 (géré par pixi)
- Contrôleur ABB sous RobotWare 6, accessible sur le réseau

---

## Installation rapide (en tant que dépendance)

```bash
pip install git+https://gitlab.ensam.eu/lcfc/abb_rws_client_python_rw6.git
```

---

## Configuration de l'environnement de développement

```bash
# 1. Cloner le dépôt
git clone https://gitlab.ensam.eu/lcfc/abb_rws_client_python_rw6.git
cd abb_rws_client_python_rw6

# 2. Installer l'environnement (pixi résout tout automatiquement)
pixi install

# 3. Copier et renseigner les variables d'environnement
cp .env.example .env
# Éditer .env avec l'IP du robot et les identifiants

# 4. Lancer les tests
pixi run test

# 5. Lint / formatage
pixi run lint
pixi run format
```

---

## Configuration

Toutes les options sont lues depuis des variables d'environnement (fichier `.env`) :

| Variable             | Défaut           | Description                          |
| -------------------- | ---------------- | ------------------------------------ |
| `ROBOT_IP`         | ---               | Adresse IP du contrôleur ABB         |
| `RWS_USER`         | `Default User` | Nom d'utilisateur RWS                |
| `RWS_PASSWORD`     | `robotics`     | Mot de passe RWS                     |
| `RWS_TIMEOUT`      | ---            | Délai d'attente HTTP (secondes)      |
| `RWS_RAPID_TASK`   | `T_ROB1`       | Nom de la tâche RAPID cible          |
| `RWS_LOG_LEVEL`    | `INFO`         | Niveau de verbosité des logs         |

---

## Architecture

```
abb_rws_client/
├── core/
│   ├── client.py        # RWSClient (async) + RWSClientSync
│   ├── exceptions.py    # Hiérarchie d'exceptions personnalisées
│   ├── serializers.py   # Types RAPID ↔ Python
│   ├── env.py           # Chargeur .env
│   └── logger.py       # Logger de la bibliothèque
├── rws/                 # 1 fonction = 1 endpoint HTTP  ← AUTO-GÉNÉRÉ
│   ├── ctrl/
│   ├── iosystem/
│   ├── rapid/
│   ├── users/
│   └── ...              # cfg, elog, panel, motionsystem, vision…
└── highlevel/           # Wrappers composés (pas d'HTTP direct)
```

> `rws/` est **auto-généré** par `utils/generator/main.py`.
> Ne pas l'éditer manuellement.

---

## Licence

Ce projet est distribué sous licence **MIT** — voir le fichier [`LICENSE`](./LICENSE) pour le texte complet.  
© 2026 RACINET Clément
