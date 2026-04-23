import pytest

from buckaroo.exceptions._buckaroo_error import BuckarooError
from buckaroo.exceptions._parameter_validation_error import (
    ParameterValidationError,
    RequiredParameterMissingError,
)


def test_parameter_validation_error_is_subclass_of_buckaroo_error():
    assert issubclass(ParameterValidationError, BuckarooError)


def test_required_parameter_missing_error_is_subclass_of_parameter_validation_error():
    assert issubclass(RequiredParameterMissingError, ParameterValidationError)


def test_required_parameter_missing_error_is_subclass_of_buckaroo_error():
    assert issubclass(RequiredParameterMissingError, BuckarooError)


def test_parameter_validation_error_message_only():
    err = ParameterValidationError("bad parameter")
    assert str(err) == "bad parameter"
    assert err.parameter_name is None
    assert err.expected_type is None
    assert err.action is None
    assert err.service_name is None


def test_parameter_validation_error_all_fields():
    err = ParameterValidationError(
        "bad parameter",
        parameter_name="issuer",
        expected_type="str",
        action="Pay",
        service_name="ideal",
    )
    assert str(err) == "bad parameter"
    assert err.parameter_name == "issuer"
    assert err.expected_type == "str"
    assert err.action == "Pay"
    assert err.service_name == "ideal"


def test_parameter_validation_error_caught_as_buckaroo_error():
    try:
        raise ParameterValidationError("boom")
    except BuckarooError as caught:
        assert isinstance(caught, ParameterValidationError)
    else:
        pytest.fail("ParameterValidationError was not caught by except BuckarooError")


def test_required_parameter_missing_error_minimal():
    err = RequiredParameterMissingError("issuer")
    assert err.parameter_name == "issuer"
    assert err.action is None
    assert err.service_name is None
    assert str(err) == "Required parameter 'issuer' is missing"


def test_required_parameter_missing_error_with_service_and_action():
    err = RequiredParameterMissingError("issuer", action="Pay", service_name="ideal")
    msg = str(err)
    assert "issuer" in msg
    assert "ideal" in msg
    assert "Pay" in msg
    assert msg == "Required parameter 'issuer' is missing for ideal Pay action"
    assert err.parameter_name == "issuer"
    assert err.action == "Pay"
    assert err.service_name == "ideal"


def test_required_parameter_missing_error_with_only_action():
    err = RequiredParameterMissingError("issuer", action="Pay")
    assert str(err) == "Required parameter 'issuer' is missing for Pay action"


def test_required_parameter_missing_error_with_only_service():
    err = RequiredParameterMissingError("issuer", service_name="ideal")
    assert str(err) == "Required parameter 'issuer' is missing for ideal"


def test_required_parameter_missing_error_caught_as_parameter_validation_error():
    try:
        raise RequiredParameterMissingError("issuer", action="Pay", service_name="ideal")
    except ParameterValidationError as caught:
        assert isinstance(caught, RequiredParameterMissingError)
    else:
        pytest.fail(
            "RequiredParameterMissingError was not caught by except ParameterValidationError"
        )
