# abb_rws_client/mastership.py
"""
Gestion du Mastership RAPID pour ABB RobotWare 6.

Qu'est-ce que le mastership ?
    Le mastership est un verrou exclusif côté contrôleur ABB qui autorise
    les opérations d'écriture sur les variables RAPID et la configuration.
    Un seul client peut détenir le mastership à la fois.

Pourquoi un context manager ?
    Le mastership DOIT être libéré dans tous les cas, même si une exception
    survient pendant l'écriture. Un mastership non libéré bloque toute
    écriture depuis n'importe quel autre client (y compris RobotStudio)
    jusqu'au redémarrage du contrôleur ou à un timeout ABB (~30s).
    Le context manager async garantit la libération via le bloc finally
    de __aexit__, quelle que soit la raison de sortie du bloc.

Endpoints RWS utilisés :
    POST /rw/mastership/request  → acquisition  (réponse attendue : 204)
    POST /rw/mastership/release  → libération    (réponse attendue : 204)

Conditions de refus (MastershipDenied) :
    - Le programme RAPID tourne en mode automatique
    - Un autre client détient déjà le mastership
    - Le contrôleur est en état d'erreur

Usage recommandé :
    Le mastership doit être détenu le moins longtemps possible.
    Pattern correct ::

        async with RWSClient(...) as client:
            # Watchdog / lecture — PAS de mastership nécessaire
            state = await client.get("rw/rapid/execution", params={"json": "1"})

            # Écriture ponctuelle — mastership court
            async with Mastership(client) as ms:
                await set_rapid_var(client, "TARGET", new_value, "robtarget")
            # mastership libéré ici automatiquement

    Pattern incorrect (mastership trop long) ::

        async with Mastership(client):
            while True:  # ← NE PAS FAIRE : bloque tout autre client
                await asyncio.sleep(1)
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

from abb_rws_client.client import RWSClient
from abb_rws_client.exceptions import MastershipDenied, MastershipNotHeld

logger = logging.getLogger(__name__)

# Endpoints RWS mastership
_MASTERSHIP_REQUEST_PATH = "rw/mastership/request"
_MASTERSHIP_RELEASE_PATH = "rw/mastership/release"

# Codes HTTP valides pour les actions mastership
# RWS retourne 204 No Content sur succès, parfois 200 selon la version RW6
_MASTERSHIP_SUCCESS_CODES = {200, 204}


class Mastership:
    """Context manager async pour l'acquisition et la libération du mastership RAPID.

    Garantit que le mastership est TOUJOURS libéré, même en cas d'exception,
    via le bloc finally de __aexit__.

    Ce context manager est réentrant par conception : si le mastership est
    déjà détenu (held=True), une nouvelle entrée dans le context manager
    ne fait pas de requête supplémentaire et ne libère pas à la sortie.
    Cela permet l'imbrication sans double-acquisition.

    Example:
        Utilisation standard ::

            async with RWSClient(host="192.168.125.1") as client:
                async with Mastership(client) as ms:
                    # mastership détenu ici
                    await set_rapid_var(client, "SPEED", 100.0, "num")
                # mastership libéré ici

        Vérification de l'état ::

            ms = Mastership(client)
            print(ms.held)  # False
            async with ms:
                print(ms.held)  # True
            print(ms.held)  # False

    Args:
        client: Instance de RWSClient ouverte.

    Attributes:
        held: True si le mastership est actuellement détenu par ce contexte.

    Raises:
        MastershipDenied: Si le contrôleur refuse l'acquisition.
        MastershipNotHeld: Si une tentative de libération est faite sans
                           détenir le mastership (ne devrait pas arriver
                           en usage normal via context manager).
    """

    def __init__(self, client: RWSClient) -> None:
        self._client = client
        #: True si ce contexte détient actuellement le mastership
        self.held: bool = False
        #: Compteur de réentrance — incrémenté à chaque __aenter__ imbriqué
        self._depth: int = 0

    async def __aenter__(self) -> Self:
        """Acquiert le mastership auprès du contrôleur.

        En cas de réentrance (depth > 0), ne fait pas de requête supplémentaire
        et incrémente simplement le compteur de profondeur.

        Raises:
            MastershipDenied: Le contrôleur a refusé l'acquisition.
        """
        if self._depth == 0:
            await self._request_mastership()
        self._depth += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Libère le mastership.

        Utilise un bloc try/finally pour garantir la libération même si
        une exception est en cours de propagation. La libération est
        tentée même en cas d'erreur — un mastership non libéré est pire
        qu'une exception supplémentaire lors de la libération.

        Note : __aexit__ ne supprime pas les exceptions (retourne None/False),
        ce qui permet à l'exception originale de se propager normalement.
        """
        self._depth -= 1
        if self._depth == 0:
            # Libération inconditionnelle — même si une exception est en cours
            await self._release_mastership()

    async def _request_mastership(self) -> None:
        """Envoie la requête d'acquisition du mastership au contrôleur.

        Raises:
            MastershipDenied: Si le contrôleur retourne 403 ou un status
                              indiquant un refus.
        """
        logger.debug("Requesting RAPID mastership — host=%s", self._client._host)
        try:
            response = await self._client.post(_MASTERSHIP_REQUEST_PATH)
        except Exception as exc:
            # Toute erreur réseau/HTTP lors de l'acquisition est wrappée
            # en MastershipDenied pour simplifier le catch côté utilisateur
            raise MastershipDenied(
                f"Failed to acquire mastership: {exc}"
            ) from exc

        if response.status_code not in _MASTERSHIP_SUCCESS_CODES:
            raise MastershipDenied(
                f"Mastership request returned unexpected status {response.status_code}"
            )

        self.held = True
        logger.info("RAPID mastership acquired — host=%s", self._client._host)

    async def _release_mastership(self) -> None:
        """Envoie la requête de libération du mastership au contrôleur.

        Cette méthode est appelée dans un contexte finally — elle ne doit
        jamais lever d'exception non gérée pour ne pas masquer une exception
        originale. Les erreurs de libération sont loggées en WARNING.

        Raises:
            MastershipNotHeld: Si held=False au moment de la libération
                               (indique un bug dans la logique d'appel).
        """
        if not self.held:
            # Cas défensif : ne devrait pas arriver en usage normal
            raise MastershipNotHeld()

        logger.debug("Releasing RAPID mastership — host=%s", self._client._host)
        try:
            await self._client.post(_MASTERSHIP_RELEASE_PATH)
            self.held = False
            logger.info("RAPID mastership released — host=%s", self._client._host)
        except Exception as exc:
            # On logue mais on ne re-lève PAS : on est potentiellement dans
            # un finally suite à une exception. Masquer l'exception originale
            # serait pire que de laisser le mastership dans un état incertain.
            # Le contrôleur ABB a un timeout de ~30s qui libère automatiquement.
            logger.warning(
                "Failed to release mastership (will timeout on controller): %s",
                exc,
            )
            self.held = False  # état local mis à jour malgré l'erreur réseau

    def __repr__(self) -> str:
        return (
            f"Mastership("
            f"held={self.held}, "
            f"depth={self._depth}, "
            f"host={self._client._host!r})"
        )
