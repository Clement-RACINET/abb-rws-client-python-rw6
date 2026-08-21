# tests/test_exceptions.py
# Copyright (c) 2026 Clément RACINET
"""
Unit tests for abb_rws_client_python_rw6.core.exceptions — no robot required.

Author: Clement RACINET

Coverage:
- RWSError base class: message, status_code, str, repr
- Full inheritance hierarchy
- Exception-specific behaviour: default messages, status codes, attributes
- All custom exceptions catchable as a single RWSError
"""

import pytest

from abb_rws_client_python_rw6.core.exceptions import (
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
# RWSError — base class
# ---------------------------------------------------------------------------


class TestRWSError:
    def test_message_stored(self) -> None:
        """The message argument must be stored on the exception instance."""
        exc = RWSError("something went wrong")
        assert exc.message == "something went wrong"

    def test_status_code_none_by_default(self) -> None:
        """status_code must default to None when not provided."""
        exc = RWSError("oops")
        assert exc.status_code is None

    def test_status_code_stored(self) -> None:
        """A provided status_code must be stored on the exception instance."""
        exc = RWSError("bad request", status_code=400)
        assert exc.status_code == 400

    def test_str_is_message(self) -> None:
        """str() must return the error message."""
        exc = RWSError("hello")
        assert str(exc) == "hello"

    def test_repr_without_status_code(self) -> None:
        """repr() without status_code must only include the message."""
        exc = RWSError("hello")
        assert repr(exc) == "RWSError(message='hello')"

    def test_repr_with_status_code(self) -> None:
        """repr() with status_code must include both message and status_code."""
        exc = RWSError("bad", status_code=503)
        assert repr(exc) == "RWSError(message='bad', status_code=503)"

    def test_is_exception(self) -> None:
        """RWSError must be raiseable and catchable as a standard exception."""
        with pytest.raises(RWSError):
            raise RWSError("test")


# ---------------------------------------------------------------------------
# Inheritance hierarchy
# ---------------------------------------------------------------------------


class TestInheritanceHierarchy:
    def test_connection_error_is_rws_error(self) -> None:
        """RWSConnectionError must be a subclass of RWSError."""
        assert issubclass(RWSConnectionError, RWSError)

    def test_timeout_error_is_rws_error(self) -> None:
        """RWSTimeoutError must be a subclass of RWSError."""
        assert issubclass(RWSTimeoutError, RWSError)

    def test_auth_error_is_rws_error(self) -> None:
        """RWSAuthenticationError must be a subclass of RWSError."""
        assert issubclass(RWSAuthenticationError, RWSError)

    def test_http_error_is_rws_error(self) -> None:
        """RWSHTTPError must be a subclass of RWSError."""
        assert issubclass(RWSHTTPError, RWSError)

    def test_not_found_is_http_error(self) -> None:
        """RWSNotFoundError must be a subclass of RWSHTTPError."""
        assert issubclass(RWSNotFoundError, RWSHTTPError)

    def test_mastership_error_is_rws_error(self) -> None:
        """MastershipError must be a subclass of RWSError."""
        assert issubclass(MastershipError, RWSError)

    def test_mastership_denied_is_mastership_error(self) -> None:
        """MastershipDenied must be a subclass of MastershipError."""
        assert issubclass(MastershipDenied, MastershipError)

    def test_mastership_not_held_is_mastership_error(self) -> None:
        """MastershipNotHeld must be a subclass of MastershipError."""
        assert issubclass(MastershipNotHeld, MastershipError)

    def test_value_error_is_rws_error(self) -> None:
        """RWSValueError must be a subclass of RWSError."""
        assert issubclass(RWSValueError, RWSError)

    def test_all_catchable_as_rws_error(self) -> None:
        """Every custom exception must be catchable with a single except RWSError."""
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
# Exception-specific behaviour
# ---------------------------------------------------------------------------


class TestRWSAuthenticationError:
    def test_default_message(self) -> None:
        """Default message must reference HTTP 401."""
        exc = RWSAuthenticationError()
        assert "401" in exc.message

    def test_status_code_is_401(self) -> None:
        """status_code must always be 401."""
        exc = RWSAuthenticationError()
        assert exc.status_code == 401

    def test_custom_message(self) -> None:
        """A custom message must be stored as-is."""
        exc = RWSAuthenticationError("custom auth error")
        assert exc.message == "custom auth error"


class TestRWSNotFoundError:
    def test_resource_stored(self) -> None:
        """The resource path must be stored on the exception instance."""
        exc = RWSNotFoundError("rw/rapid/symbol/data/RAPID/T_ROB1/TRAJCENTER/SPEED")
        assert exc.resource == "rw/rapid/symbol/data/RAPID/T_ROB1/TRAJCENTER/SPEED"

    def test_status_code_is_404(self) -> None:
        """status_code must always be 404."""
        exc = RWSNotFoundError("some/path")
        assert exc.status_code == 404

    def test_message_contains_resource(self) -> None:
        """The error message must include the resource path."""
        exc = RWSNotFoundError("some/path")
        assert "some/path" in exc.message

    def test_repr_contains_class_name(self) -> None:
        """repr() must include the class name."""
        exc = RWSNotFoundError("some/path")
        assert "RWSNotFoundError" in repr(exc)


class TestMastershipDenied:
    def test_default_message(self) -> None:
        """Default message must mention that mastership was denied."""
        exc = MastershipDenied()
        assert "denied" in exc.message.lower()

    def test_custom_message(self) -> None:
        """A custom message must be stored as-is."""
        exc = MastershipDenied("controller in auto mode")
        assert exc.message == "controller in auto mode"

    def test_status_code_is_none(self) -> None:
        """MastershipDenied must not carry an HTTP status code."""
        exc = MastershipDenied()
        assert exc.status_code is None


class TestMastershipNotHeld:
    def test_default_message(self) -> None:
        """Default message must mention mastership."""
        exc = MastershipNotHeld()
        assert "mastership" in exc.message.lower()

    def test_status_code_is_none(self) -> None:
        """MastershipNotHeld must not carry an HTTP status code."""
        exc = MastershipNotHeld()
        assert exc.status_code is None

    def test_repr(self) -> None:
        """repr() must include the class name."""
        exc = MastershipNotHeld()
        assert "MastershipNotHeld" in repr(exc)


class TestRWSConnectionError:
    def test_message_and_no_status(self) -> None:
        """Message must be stored and status_code must be None."""
        exc = RWSConnectionError("unreachable")
        assert exc.message == "unreachable"
        assert exc.status_code is None


class TestRWSTimeoutError:
    def test_message_and_no_status(self) -> None:
        """Message must be stored and status_code must be None."""
        exc = RWSTimeoutError("timed out after 10s")
        assert exc.status_code is None
        assert "10s" in exc.message


class TestRWSValueError:
    def test_message(self) -> None:
        """Message must be stored and accessible."""
        exc = RWSValueError("invalid robtarget format")
        assert "robtarget" in exc.message
