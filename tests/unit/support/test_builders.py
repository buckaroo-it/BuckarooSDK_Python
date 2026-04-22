"""Tests for tests.support.builders.make_test_builder."""

from __future__ import annotations

from unittest.mock import MagicMock

from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
    AuthorizeCaptureCapable,
)
from buckaroo.builders.payments.capabilities.encrypted_pay_capable import (
    EncryptedPayCapable,
)
from tests.support.builders import make_test_builder


def _client():
    return MagicMock()


def test_returns_payment_builder_subclass_instance_bound_to_client():
    client = _client()
    builder = make_test_builder(client)

    assert isinstance(builder, PaymentBuilder)
    assert builder._client is client


def test_service_name_kwarg_sets_service_name_attr_and_getter():
    builder = make_test_builder(_client(), service_name="creditcard")

    assert builder._serviceName == "creditcard"
    assert builder.get_service_name() == "creditcard"


def test_allowed_params_returned_per_action_empty_dict_for_unknown():
    allowed = {
        "Pay": {"a": {"type": str}, "b": {"type": str}},
        "Refund": {"x": {"type": str}},
    }
    builder = make_test_builder(_client(), allowed_params=allowed)

    assert builder.get_allowed_service_parameters("Pay") == allowed["Pay"]
    assert builder.get_allowed_service_parameters("Refund") == allowed["Refund"]
    assert builder.get_allowed_service_parameters("Unknown") == {}


def test_capabilities_mix_in_their_methods():
    builder = make_test_builder(
        _client(),
        capabilities=(EncryptedPayCapable, AuthorizeCaptureCapable),
    )

    assert isinstance(builder, EncryptedPayCapable)
    assert isinstance(builder, AuthorizeCaptureCapable)
    # Concrete methods from the mixins must be present and callable
    assert callable(getattr(builder, "payEncrypted"))
    assert callable(getattr(builder, "authorize"))
    assert callable(getattr(builder, "capture"))
    assert callable(getattr(builder, "cancelAuthorize"))
