# abb-rws-client-python-rw6

Async Python client library for ABB robot controllers via the
[Robot Web Services (RWS)](https://developercenter.robotstudio.com/api/rwsApi/)
API under **RobotWare 6**.

> **RobotWare 7 / OmniCore is out of scope.**

---

## Features

| Domain           | Operations                                                                   |
| ---------------- | ---------------------------------------------------------------------------- |
| Session          | HTTP Digest authentication, ABBCX cookie, automatic retry                    |
| RAPID Mastership | Acquire / release (`async with` context manager)                             |
| RAPID Variables  | `get` / `set` — `num`, `bool`, `string`, `array`, `robtarget`                |
| RAPID Execution  | Read / control execution state (`running` / `stopped`)                       |
| IO Signals       | Read / write digital & analog signals                                        |
| Controller       | Panel, motion system, CFG, elog, file service, subscriptions                 |
| Coverage         | 710 unit tests — 99% coverage — `ruff` clean                                 |

---

## Requirements

- [pixi](https://pixi.sh) ≥ 0.20
- Python 3.11 (managed by pixi)
- ABB controller running RobotWare 6, reachable over the network

---

## Quick install (as a dependency)

```bash
pip install git+https://gitlab.ensam.eu/lcfc/abb-rws-client-python-rw6.git
```

---

## Development setup

```bash
# 1. Clone the repository
git clone https://gitlab.ensam.eu/lcfc/abb-rws-client-python-rw6.git
cd abb-rws-client-python-rw6

# 2. Install the environment (pixi resolves everything automatically)
pixi install

# 3. Copy and fill in the environment variables
cp .env.example .env
# Edit .env with the robot IP and credentials

# 4. Run the tests
pixi run test

# 5. Lint / format
pixi run lint
pixi run format
```

---

## Configuration

All options are read from environment variables (`.env` file):

| Variable             | Default          | Description               |
| -------------------- | ---------------- | ------------------------- |
| `ROBOT_IP`         | ---               | ABB controller IP address |
| `RWS_USER`         | `Default User` | RWS username              |
| `RWS_PASSWORD`     | `robotics`     | RWS password              |
| `RWS_TIMEOUT`      | ---            | HTTP timeout (seconds)    |
| `RWS_RAPID_TASK`   | `T_ROB1`       | Target RAPID task name    |
| `RWS_LOG_LEVEL`    | `T_ROB1`       | Target RAPID task name    |

---

## Architecture

```
abb_rws_client/
├── _core/
│   ├── client.py        # RWSClient (async) + RWSClientSync
│   ├── exceptions.py    # Custom exception hierarchy
│   ├── serializers.py   # RAPID types ↔ Python
│   ├── env.py           # .env loader
│   └── logging.py       # Library logger
├── rws/                 # 1 function = 1 HTTP endpoint  ← AUTO-GENERATED
│   ├── ctrl/
│   ├── iosystem/
│   ├── rapid/
│   ├── users/
│   └── ...              # cfg, elog, panel, motionsystem, vision…
└── highlevel/           # Composed wrappers (no direct HTTP)
```

> `rws/` is **auto-generated** by `contrib/generator/main.py`.
> Do not edit it manually.

---

## License

Internal project — LCFC / ENSAM. All rights reserved.
