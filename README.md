
# abb-rws6-python-client

Bibliothèque Python **async** pour piloter un contrôleur ABB via
l'API [Robot Web Services (RWS)](https://developercenter.robotstudio.com/api/rwsApi/)
sous **RobotWare 6**.

## Fonctionnalités

| Domaine          | Opérations                                                                  |
| ---------------- | ---------------------------------------------------------------------------- |
| Session          | Authentification HTTP Digest, cookie ABBCX, retry automatique                |
| Mastership RAPID | Acquisition / libération (context manager`async with`)                    |
| Variables RAPID  | `get` / `set` — `num`, `bool`, `string`, `array`, `robtarget` |
| Exécution RAPID | Lecture de l'état (`running` / `stopped`)                               |

## Prérequis

- [pixi](https://pixi.sh) ≥ 0.20
- Python 3.11 (géré par pixi)
- Contrôleur ABB sous RobotWare 6 accessible en réseau

## Installation rapide (comme dépendance)

```bash
pip install git+https://github.com/<ton-org>/abb-rws6-python-client.git

# 1. Cloner le repo
git clone https://github.com/<ton-org>/abb-rws6-python-client.git
cd abb-rws6-python-client

# 2. Installer l'environnement (pixi résout tout automatiquement)
pixi install

# 3. Copier et renseigner les variables d'environnement
cp .env.example .env
# éditer .env avec l'IP et les credentials du robot

# 4. Lancer les tests
pixi run test

# 5. Linter / formatter
pixi run lint
pixi run format

```


## Configuration

Toutes les options sont lues depuis les variables d'environnement (fichier `.env`) :

| Variable | Défaut | Description |
|---|---|---|
| `ROBOT_IP` | — | IP du contrôleur ABB |
| `RWS_USER` | `Default User` | Utilisateur RWS |
| `RWS_PASSWORD` | `robotics` | Mot de passe RWS |
| `RWS_TIMEOUT` | `10` | Timeout HTTP (secondes) |
| `RWS_RAPID_MODULE` | `TRAJCENTER` | Module RAPID cible | xxx
| `RWS_RAPID_TASK` | `T_ROB1` | Tâche RAPID cible |
