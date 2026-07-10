
# abb-rws6-python-client

Bibliothèque Python **async** pour piloter un contrôleur ABB via
l'API [Robot Web Services (RWS)](https://developercenter.robotstudio.com/api/rwsApi/)
sous **RobotWare 6**.

> **RobotWare 7 / OmniCore hors périmètre.**

---

## Fonctionnalités

| Domaine           | Opérations                                                                  |
|-------------------|-----------------------------------------------------------------------------|
| Session           | Authentification HTTP Digest, cookie ABBCX, retry automatique               |
| Mastership RAPID  | Acquisition / libération (context manager `async with`)                     |
| Variables RAPID   | `get` / `set` — `num`, `bool`, `string`, `array`, `robtarget`               |
| Exécution RAPID   | Lecture de l'état (`running` / `stopped`)                                   |

---

## Prérequis

- [pixi](https://pixi.sh) ≥ 0.20
- Python 3.11 (géré par pixi)
- Contrôleur ABB sous RobotWare 6 accessible en réseau

---

## Installation rapide (comme dépendance)

```bash
pip install git+https://gitlab.ensam.eu/lcfc/abb-rws-client-python-rw6.git
```

---

## Installation pour le développement

```bash
# 1. Cloner le dépôt
git clone https://gitlab.ensam.eu/lcfc/abb-rws-client-python-rw6.git
cd abb-rws-client-python-rw6

# 2. Installer l'environnement (pixi résout tout automatiquement)
pixi install

# 3. Copier et renseigner les variables d'environnement
cp .env.example .env
# Éditer .env avec l'IP et les credentials du robot

# 4. Lancer les tests
pixi run test

# 5. Linter / formatter
pixi run lint
pixi run format
```

---

## Configuration

Toutes les options sont lues depuis les variables d'environnement (fichier `.env`) :

| Variable             | Défaut          | Description               |
| -------------------- | ---------------- | ------------------------- |
| `ROBOT_IP`         | —               | IP du contrôleur ABB     |
| `RWS_USER`         | `Default User` | Utilisateur RWS           |
| `RWS_PASSWORD`     | `robotics`     | Mot de passe RWS          |
| `RWS_TIMEOUT`      | `10`           | Timeout HTTP (secondes)   |
| `RWS_RAPID_MODULE` | —               | Nom du module RAPID cible |
| `RWS_RAPID_TASK`   | `T_ROB1`       | Tâche RAPID cible        |

---

## Architecture

```
abb_rws_client/
├── _core/
│   ├── client.py        # RWSClient (async) + RWSClientSync
│   ├── exceptions.py    # Hiérarchie d'exceptions custom
│   └── serializers.py   # Types RAPID ↔ Python
├── rws/                 # 1 fonction = 1 endpoint HTTP  ← GÉNÉRÉ AUTOMATIQUEMENT
│   ├── ctrl/
│   ├── rapid/
│   └── ...
└── highlevel/           # Wrappers composés (pas d'HTTP direct)
```

> `rws/` est **généré automatiquement** par `contrib/generator/main.py`.
> Ne pas modifier manuellement.

---

## Licence

Projet interne — LCFC / ENSAM. Tous droits réservés.
