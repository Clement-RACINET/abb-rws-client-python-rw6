# tests/test_exceptions.py
"""Tests unitaires pour abb_rws_client.exceptions — aucun robot requis."""

import pytest

from abb_rws_client._core.exceptions import (
    MastershipDenied,
    MastershipError,
    MastershipNotHeld,
    RWSAuthenticationError,
    RWSConnectionError,
    RWSError,
    RWSHTTPError,
    RWSNotFoundError,
    RWSTimeoutError,
    RWSValueError,
)

# ---------------------------------------------------------------------------
# RWSError — classe racine
# ---------------------------------------------------------------------------


class TestRWSError:
    def test_message_stored(self) -> None:
        exc = RWSError("something went wrong")
        assert exc.message == "something went wrong"

    def test_status_code_none_by_default(self) -> None:
        exc = RWSError("oops")
        assert exc.status_code is None

    def test_status_code_stored(self) -> None:
        exc = RWSError("bad request", status_code=400)
        assert exc.status_code == 400

    def test_str_is_message(self) -> None:
        exc = RWSError("hello")
        assert str(exc) == "hello"

    def test_repr_without_status_code(self) -> None:
        exc = RWSError("hello")
        assert repr(exc) == "RWSError(message='hello')"

    def test_repr_with_status_code(self) -> None:
        exc = RWSError("bad", status_code=503)
        assert repr(exc) == "RWSError(message='bad', status_code=503)"

    def test_is_exception(self) -> None:
        with pytest.raises(RWSError):
            raise RWSError("test")


# ---------------------------------------------------------------------------
# Hiérarchie d'héritage
# ---------------------------------------------------------------------------


class TestInheritanceHierarchy:
    def test_connection_error_is_rws_error(self) -> None:
        assert issubclass(RWSConnectionError, RWSError)

    def test_timeout_error_is_rws_error(self) -> None:
        assert issubclass(RWSTimeoutError, RWSError)

    def test_auth_error_is_rws_error(self) -> None:
        assert issubclass(RWSAuthenticationError, RWSError)

    def test_http_error_is_rws_error(self) -> None:
        assert issubclass(RWSHTTPError, RWSError)

    def test_not_found_is_http_error(self) -> None:
        assert issubclass(RWSNotFoundError, RWSHTTPError)

    def test_mastership_error_is_rws_error(self) -> None:
        assert issubclass(MastershipError, RWSError)

    def test_mastership_denied_is_mastership_error(self) -> None:
        assert issubclass(MastershipDenied, MastershipError)

    def test_mastership_not_held_is_mastership_error(self) -> None:
        assert issubclass(MastershipNotHeld, MastershipError)

    def test_value_error_is_rws_error(self) -> None:
        assert issubclass(RWSValueError, RWSError)

    def test_all_catchable_as_rws_error(self) -> None:
        """Toutes les exceptions custom sont catchables en un seul except RWSError."""
        exceptions = [
            RWSConnectionError("x"),
            RWSTimeoutError("x"),
            RWSAuthenticationError(),
            RWSHTTPError("x"),
            RWSNotFoundError("x"),
            MastershipDenied(),
            MastershipNotHeld(),
            RWSValueError("x"),
        ]
        for exc in exceptions:
            with pytest.raises(RWSError):
                raise exc


# ---------------------------------------------------------------------------
# Exceptions avec comportement spécifique
# ---------------------------------------------------------------------------


class TestRWSAuthenticationError:
    def test_default_message(self) -> None:
        exc = RWSAuthenticationError()
        assert "401" in exc.message

    def test_status_code_is_401(self) -> None:
        exc = RWSAuthenticationError()
        assert exc.status_code == 401

    def test_custom_message(self) -> None:
        exc = RWSAuthenticationError("custom auth error")
        assert exc.message == "custom auth error"


class TestRWSNotFoundError:
    def test_resource_stored(self) -> None:
        exc = RWSNotFoundError("rw/rapid/symbol/data/RAPID/T_ROB1/TRAJCENTER/SPEED")
        assert exc.resource == "rw/rapid/symbol/data/RAPID/T_ROB1/TRAJCENTER/SPEED"

    def test_status_code_is_404(self) -> None:
        exc = RWSNotFoundError("some/path")
        assert exc.status_code == 404

    def test_message_contains_resource(self) -> None:
        exc = RWSNotFoundError("some/path")
        assert "some/path" in exc.message

    def test_repr_contains_class_name(self) -> None:
        exc = RWSNotFoundError("some/path")
        assert "RWSNotFoundError" in repr(exc)


class TestMastershipDenied:
    def test_default_message(self) -> None:
        exc = MastershipDenied()
        assert "denied" in exc.message.lower()

    def test_custom_message(self) -> None:
        exc = MastershipDenied("controller in auto mode")
        assert exc.message == "controller in auto mode"

    def test_status_code_is_none(self) -> None:
        exc = MastershipDenied()
        assert exc.status_code is None


class TestMastershipNotHeld:
    def test_default_message(self) -> None:
        exc = MastershipNotHeld()
        assert "mastership" in exc.message.lower()

    def test_status_code_is_none(self) -> None:
        exc = MastershipNotHeld()
        assert exc.status_code is None

    def test_repr(self) -> None:
        exc = MastershipNotHeld()
        assert "MastershipNotHeld" in repr(exc)


class TestRWSConnectionError:
    def test_message_and_no_status(self) -> None:
        exc = RWSConnectionError("unreachable")
        assert exc.message == "unreachable"
        assert exc.status_code is None


class TestRWSTimeoutError:
    def test_message_and_no_status(self) -> None:
        exc = RWSTimeoutError("timed out after 10s")
        assert exc.status_code is None
        assert "10s" in exc.message


class TestRWSValueError:
    def test_message(self) -> None:
        exc = RWSValueError("invalid robtarget format")
        assert "robtarget" in exc.message
