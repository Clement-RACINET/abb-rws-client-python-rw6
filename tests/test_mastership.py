# tests/test_mastership.py
"""
Tests unitaires pour Mastership — utilise httpx.MockTransport, aucun robot requis.

Stratégie de mock :
    httpx.AsyncClient accepte un paramètre `transport` qui remplace la couche
    réseau réelle. On injecte un MockTransport qui retourne des réponses
    prédéfinies, ce qui permet de tester toute la logique sans contrôleur.

    On sous-classe RWSClient pour injecter le transport mocké sans modifier
    l'interface publique.
"""

from __future__ import annotations

import httpx
import pytest

from old_abb_rws_client.client import RWSClient
from old_abb_rws_client.exceptions import MastershipDenied, MastershipNotHeld
from old_abb_rws_client.mastership import Mastership

# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------


def _make_response(status_code: int, content: bytes = b"") -> httpx.Response:
    """Crée une httpx.Response minimale pour les tests."""
    return httpx.Response(status_code=status_code, content=content)


class _MockTransport(httpx.AsyncBaseTransport):
    """Transport httpx mocké : retourne des réponses prédéfinies par chemin."""

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        """
        Args:
            routes: Mapping chemin → réponse.
                    Exemple : {"rw/mastership/request": httpx.Response(204)}
        """
        self._routes = routes
        #: Historique des requêtes reçues, pour assertions
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        # Cherche le chemin dans les routes (sans query string)
        path = request.url.path.lstrip("/")
        if path in self._routes:
            return self._routes[path]
        return _make_response(404)


async def _make_client(transport: _MockTransport) -> RWSClient:
    """Crée un RWSClient avec transport mocké et l'ouvre."""
    client = RWSClient(host="192.168.125.1")
    # Injection du transport mocké après création du AsyncClient
    client._http = httpx.AsyncClient(
        base_url=client.base_url,
        transport=transport,
        follow_redirects=True,
    )
    return client


# ---------------------------------------------------------------------------
# Tests acquisition du mastership
# ---------------------------------------------------------------------------


class TestMastershipAcquire:
    async def test_acquire_success_204(self) -> None:
        """Acquisition réussie avec réponse 204 No Content."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(204),
            "rw/mastership/release": _make_response(204),
        })
        client = await _make_client(transport)
        ms = Mastership(client)

        async with ms:
            assert ms.held is True

        assert ms.held is False

    async def test_acquire_success_200(self) -> None:
        """Acquisition réussie avec réponse 200 (certaines versions RW6)."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(200),
            "rw/mastership/release": _make_response(204),
        })
        client = await _make_client(transport)
        async with Mastership(client):
            pass  # pas d'exception = succès

    async def test_acquire_denied_403(self) -> None:
        """Le contrôleur refuse le mastership (403)."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(403),
        })
        client = await _make_client(transport)

        with pytest.raises(MastershipDenied):
            async with Mastership(client):
                pass

    async def test_held_is_false_before_enter(self) -> None:
        transport = _MockTransport({})
        client = await _make_client(transport)
        ms = Mastership(client)
        assert ms.held is False

    async def test_acquire_unexpected_2xx_raises_mastership_denied(self) -> None:
        """Status 2xx non reconnu (ex: 202) → MastershipDenied."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(202),
        })
        client = await _make_client(transport)
        with pytest.raises(MastershipDenied, match="unexpected status 202"):
            async with Mastership(client):
                pass

# ---------------------------------------------------------------------------
# Tests libération du mastership
# ---------------------------------------------------------------------------


class TestMastershipRelease:
    async def test_release_called_on_normal_exit(self) -> None:
        """La libération est appelée à la sortie normale du context manager."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(204),
            "rw/mastership/release": _make_response(204),
        })
        client = await _make_client(transport)

        async with Mastership(client):
            pass

        # Vérifie que les deux requêtes ont bien été envoyées
        paths = [r.url.path.lstrip("/") for r in transport.requests]
        assert "rw/mastership/request" in paths
        assert "rw/mastership/release" in paths

    async def test_release_called_on_exception(self) -> None:
        """La libération est appelée même si une exception survient dans le bloc."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(204),
            "rw/mastership/release": _make_response(204),
        })
        client = await _make_client(transport)
        ms = Mastership(client)

        with pytest.raises(ValueError, match="test error"):
            async with ms:
                raise ValueError("test error")

        # held doit être False malgré l'exception
        assert ms.held is False
        paths = [r.url.path.lstrip("/") for r in transport.requests]
        assert "rw/mastership/release" in paths

    async def test_release_failure_does_not_mask_original_exception(self) -> None:
        """Si la libération échoue, l'exception originale reste visible."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(204),
            # Pas de route release → 404 → exception dans _release_mastership
            # Mais _release_mastership ne re-lève pas → l'exception originale passe
        })
        client = await _make_client(transport)

        with pytest.raises(RuntimeError, match="original"):
            async with Mastership(client):
                raise RuntimeError("original")

    async def test_mastership_not_held_raises_on_manual_release(self) -> None:
        """MastershipNotHeld si on tente de libérer sans détenir."""
        transport = _MockTransport({})
        client = await _make_client(transport)
        ms = Mastership(client)

        with pytest.raises(MastershipNotHeld):
            await ms._release_mastership()


# ---------------------------------------------------------------------------
# Tests réentrance
# ---------------------------------------------------------------------------


class TestMastershipReentrance:
    async def test_nested_context_managers_single_request(self) -> None:
        """Deux context managers imbriqués ne font qu'une seule acquisition."""
        transport = _MockTransport({
            "rw/mastership/request": _make_response(204),
            "rw/mastership/release": _make_response(204),
        })
        client = await _make_client(transport)
        ms = Mastership(client)

        async with ms:
            async with ms:
                assert ms.held is True
                assert ms._depth == 2
            # Sortie du 2e niveau — pas encore libéré
            assert ms.held is True
            assert ms._depth == 1

        # Sortie du 1er niveau — libéré
        assert ms.held is False

        # Une seule requête request, une seule release
        paths = [r.url.path.lstrip("/") for r in transport.requests]
        assert paths.count("rw/mastership/request") == 1
        assert paths.count("rw/mastership/release") == 1


# ---------------------------------------------------------------------------
# Tests repr
# ---------------------------------------------------------------------------


class TestMastershipRepr:
    async def test_repr_closed(self) -> None:
        transport = _MockTransport({})
        client = await _make_client(transport)
        ms = Mastership(client)
        assert "held=False" in repr(ms)
        assert "192.168.125.1" in repr(ms)
