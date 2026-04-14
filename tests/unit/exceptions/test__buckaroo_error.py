"""Tests for buckaroo.exceptions._buckaroo_error.BuckarooError."""

import pytest

from buckaroo.exceptions._buckaroo_error import BuckarooError


def test_is_subclass_of_exception():
    assert issubclass(BuckarooError, Exception)


def test_can_be_raised_and_caught():
    with pytest.raises(BuckarooError):
        raise BuckarooError("boom")


def test_message_only_round_trip():
    err = BuckarooError("something went wrong")

    assert err.args == ("something went wrong",)
    assert str(err) == "something went wrong"


def test_no_args_round_trip():
    err = BuckarooError()

    assert err.args == ()
    assert str(err) == ""


def test_positional_http_status_round_trip():
    err = BuckarooError("server exploded", 500)

    assert err.args == ("server exploded", 500)


def test_str_reflects_single_arg():
    err = BuckarooError("denied")

    assert str(err) == "denied"


def test_repr_includes_class_name_and_args():
    err = BuckarooError("denied", 401)

    rendered = repr(err)
    assert rendered.startswith("BuckarooError(")
    assert "'denied'" in rendered
    assert "401" in rendered


def test_repr_with_no_args():
    err = BuckarooError()

    assert repr(err) == "BuckarooError()"
