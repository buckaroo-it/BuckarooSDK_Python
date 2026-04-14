import pytest

from buckaroo.exceptions._authentication_error import AuthenticationError
from buckaroo.exceptions._buckaroo_error import BuckarooError


def test_is_subclass_of_buckaroo_error():
    assert issubclass(AuthenticationError, BuckarooError)


def test_caught_by_buckaroo_error_except_block():
    try:
        raise AuthenticationError("bad creds")
    except BuckarooError as caught:
        assert isinstance(caught, AuthenticationError)
    else:
        pytest.fail("AuthenticationError was not caught by except BuckarooError")


def test_constructor_args_round_trip():
    err = AuthenticationError("invalid signature", 401)
    assert err.args == ("invalid signature", 401)
    assert str(err) == str(BuckarooError("invalid signature", 401))
