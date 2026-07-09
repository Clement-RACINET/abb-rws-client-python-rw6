# abb_rws_client/rws/rapid/symbol.py
"""
Miroir 1:1 du RAPID Symbol Data Service RWS ABB RobotWare 6.

Routes couvertes :
    GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}
        → lire la valeur courante d'une variable RAPID

    PUT /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}
        → écrire la valeur courante d'une variable RAPID

Référence : ABB RobotWare 6 — Robot Web Services API — RAPID Service

Contraintes ABB :
    - La lecture (GET) ne nécessite pas le mastership.
    - L'écriture (PUT) nécessite le mastership RAPID.
    - Le chemin suit la convention :
        RAPID/{task}/{module}/{symbol}
      où task = nom de la tâche (ex: "T_ROB1"),
           module = nom du module RAPID (ex: "MainModule"),
           symbol = nom de la variable (ex: "myVar").
    - La valeur est transmise en form-data sous la clé ``value``.
    - Le paramètre ``?json=1`` retourne du JSON au lieu de XML.
    - Les variables de type ``PERS`` et ``VAR`` sont accessibles.
      Les constantes ``CONST`` sont accessibles en lecture seule.

Status  : tested
Coverage: 100%
"""

from __future__ import annotations

import httpx

from abb_rws_client._core.client import RWSClient

# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def _symbol_path(task: str, module: str, symbol: str) -> str:
    """Construit le chemin RWS pour un symbole RAPID.

    Args:
        task: Nom de la tâche RAPID (ex: ``"T_ROB1"``).
        module: Nom du module RAPID (ex: ``"MainModule"``).
        symbol: Nom de la variable RAPID (ex: ``"myVar"``).

    Returns:
        Chemin relatif RWS (ex: ``"rw/rapid/symbol/data/RAPID/T_ROB1/MainModule/myVar"``).
    """
    return f"rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}"


# ---------------------------------------------------------------------------
# Fonctions publiques
# ---------------------------------------------------------------------------


async def get_symbol_data(
    client: RWSClient,
    task: str,
    module: str,
    symbol: str,
) -> httpx.Response:
    """Lit la valeur courante d'une variable RAPID.

    Route : GET /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}

    Contraintes ABB :
        - Accessible sans mastership (lecture seule).
        - Retourne HTTP 404 si la variable n'existe pas ou si le chemin
          task/module/symbol est incorrect.
        - Retourne HTTP 400 si la variable est de type non supporté.
        - Le paramètre ``json=1`` est ajouté automatiquement pour obtenir
          du JSON plutôt que du XML.

    Args:
        client: Instance RWSClient ouverte et authentifiée.
        task: Nom de la tâche RAPID (ex: ``"T_ROB1"``).
        module: Nom du module RAPID (ex: ``"MainModule"``).
        symbol: Nom de la variable RAPID (ex: ``"myVar"``).

    Returns:
        Réponse httpx brute. Le corps JSON contient le champ ``value``
        avec la valeur de la variable sous forme de string.

    Raises:
        RWSNotFoundError: Si la variable n'existe pas (HTTP 404).
        RWSHTTPError: Sur toute autre erreur HTTP >= 400.
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     resp = await get_symbol_data(client, "T_ROB1", "MainModule", "myVar")
        ...     print(resp.json())
    """
    return await client.get(
        _symbol_path(task, module, symbol),
        params={"json": "1"},
    )


async def set_symbol_data(
    client: RWSClient,
    task: str,
    module: str,
    symbol: str,
    value: str,
) -> httpx.Response:
    """Écrit la valeur courante d'une variable RAPID.

    Route : PUT /rw/rapid/symbol/data/RAPID/{task}/{module}/{symbol}

    Contraintes ABB :
        - Nécessite le mastership RAPID (acquis via mastership_request).
        - La valeur doit être une string au format RWS correspondant au
          type RAPID de la variable (ex: ``"3.14"`` pour num,
          ``"TRUE"`` pour bool, ``"[[0,0,500],[1,0,0,0],[0,0,0,0],[9E+9,...]]"``
          pour robtarget).
        - Retourne HTTP 404 si la variable n'existe pas.
        - Retourne HTTP 400 si la valeur ne correspond pas au type.
        - Retourne HTTP 409 si le mastership n'est pas détenu.

    Args:
        client: Instance RWSClient ouverte et authentifiée.
        task: Nom de la tâche RAPID (ex: ``"T_ROB1"``).
        module: Nom du module RAPID (ex: ``"MainModule"``).
        symbol: Nom de la variable RAPID (ex: ``"myVar"``).
        value: Valeur sérialisée au format RWS (string brute).
            Utiliser ``python_to_rapid_value()`` de ``_core/serializers``
            pour construire cette string.

    Returns:
        Réponse httpx brute (HTTP 204 No Content en cas de succès).

    Raises:
        RWSNotFoundError: Si la variable n'existe pas (HTTP 404).
        RWSHTTPError: Si le mastership n'est pas détenu (HTTP 409) ou
            valeur invalide (HTTP 400).
        RWSAuthenticationError: Si la session est expirée (HTTP 401).
        RWSConnectionError: Si le contrôleur est injoignable.
        RWSTimeoutError: Si la requête dépasse le timeout configuré.

    Example:
        >>> async with RWSClient(host="192.168.125.1") as client:
        ...     await mastership_request(client)
        ...     await set_symbol_data(client, "T_ROB1", "MainModule", "myVar", "42")
    """
    return await client.put(
        _symbol_path(task, module, symbol),
        data={"value": value},
    )
