# abb_rws_client/exceptions.py
"""
Exceptions custom pour abb-rws6-python-client.

Hiérarchie :
    RWSError                        ← racine, toujours catchable en un seul except
    ├── RWSConnectionError          ← réseau inaccessible / timeout TCP
    ├── RWSTimeoutError             ← timeout HTTP dépassé
    ├── RWSAuthenticationError      ← 401 persistant après digest
    ├── RWSHTTPError                ← toute réponse HTTP >= 400 non couverte ci-dessus
    │   └── RWSNotFoundError        ← 404 (variable / ressource inexistante)
    ├── MastershipError             ← racine des erreurs mastership
    │   ├── MastershipDenied        ← contrôleur refuse l'acquisition (mode AUTO, etc.)
    │   └── MastershipNotHeld       ← tentative d'écriture sans mastership actif
    └── RWSValueError               ← valeur RAPID invalide / sérialisation échouée
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Racine
# ---------------------------------------------------------------------------


class RWSError(Exception):
    """Classe de base pour toutes les erreurs RWS.

    Attributes:
        message: Description lisible de l'erreur.
        status_code: Code HTTP associé, si applicable.
    """

    message: str
    status_code: int | None

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __repr__(self) -> str:
        if self.status_code is not None:
            return (
                f"{self.__class__.__name__}("
                f"message={self.message!r}, "
                f"status_code={self.status_code})"
            )
        return f"{self.__class__.__name__}(message={self.message!r})"


# ---------------------------------------------------------------------------
# Erreurs réseau / transport
# ---------------------------------------------------------------------------


class RWSConnectionError(RWSError):
    """Impossible d'établir la connexion TCP avec le contrôleur.

    Levée quand httpx.ConnectError ou httpx.ConnectTimeout est intercepté.
    """


class RWSTimeoutError(RWSError):
    """Le contrôleur n'a pas répondu dans le délai imparti.

    Levée quand httpx.ReadTimeout ou httpx.PoolTimeout est intercepté.
    """


# ---------------------------------------------------------------------------
# Erreurs HTTP
# ---------------------------------------------------------------------------


class RWSAuthenticationError(RWSError):
    """Authentification Digest refusée (401 persistant).

    Indique des credentials incorrects ou un utilisateur non autorisé dans l'UAS.
    """

    def __init__(self, message: str = "Authentication failed (HTTP 401)") -> None:
        super().__init__(message, status_code=401)


class RWSHTTPError(RWSError):
    """Réponse HTTP inattendue (>= 400) non couverte par une exception plus spécifique."""


class RWSNotFoundError(RWSHTTPError):
    """Ressource RWS introuvable (HTTP 404).

    Typiquement : variable RAPID inexistante, module ou tâche incorrect.
    """

    resource: str

    def __init__(self, resource: str) -> None:
        super().__init__(f"Resource not found: {resource}", status_code=404)
        self.resource = resource


# ---------------------------------------------------------------------------
# Erreurs Mastership
# ---------------------------------------------------------------------------


class MastershipError(RWSError):
    """Classe de base pour les erreurs liées au mastership RAPID."""


class MastershipDenied(MastershipError):
    """Le contrôleur a refusé l'acquisition du mastership.

    Causes typiques :
    - Le programme RAPID tourne en mode automatique.
    - Un autre client détient déjà le mastership.
    """

    def __init__(self, message: str = "Mastership request denied by controller") -> None:
        super().__init__(message, status_code=None)


class MastershipNotHeld(MastershipError):
    """Tentative d'opération d'écriture sans mastership actif.

    Levée côté client avant même d'envoyer la requête HTTP.
    """

    def __init__(self) -> None:
        super().__init__("Cannot write: mastership is not currently held")


# ---------------------------------------------------------------------------
# Erreurs de valeur / sérialisation
# ---------------------------------------------------------------------------


class RWSValueError(RWSError):
    """Valeur RAPID invalide ou échec de sérialisation / désérialisation.

    Levée par serializers.py quand le format reçu ou fourni est incorrect.
    """
