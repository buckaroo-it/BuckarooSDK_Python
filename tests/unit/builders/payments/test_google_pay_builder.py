"""Per-builder unit tests for :class:`GooglePayBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
supported action, mixin presence, and an end-to-end ``pay()`` dispatch through
``MockBuckaroo``. Phase 7.15.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.google_pay_builder import GooglePayBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = GooglePayBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_google_pay(client):
    assert GooglePayBuilder(client).get_service_name() == "GooglePay"


def test_get_allowed_service_parameters_pay_snapshot(client):
    assert GooglePayBuilder(client).get_allowed_service_parameters("Pay") == {
        "PaymentData": {"type": str, "required": True, "description": ""},
        "CustomerCardName": {"type": str, "required": False, "description": ""},
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = GooglePayBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert GooglePayBuilder(client).get_allowed_service_parameters("Refund") == {}


@pytest.mark.parametrize("method", ["pay", "refund", "build", "from_dict"])
def test_base_payment_methods_present_and_callable(client, method):
    builder = GooglePayBuilder(client)
    assert hasattr(builder, method)
    assert callable(getattr(builder, method))


def test_google_pay_mixes_in_no_capability_mixins(client):
    """GooglePayBuilder is a plain PaymentBuilder; no authorize/refund/fast-checkout mixins."""
    from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
        AuthorizeCaptureCapable,
    )
    from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
        BankTransferCapabilities,
    )
    from buckaroo.builders.payments.capabilities.encrypted_pay_capable import (
        EncryptedPayCapable,
    )
    from buckaroo.builders.payments.capabilities.fast_checkout_capable import (
        FastCheckoutCapable,
    )
    from buckaroo.builders.payments.capabilities.instant_refund_capable import (
        InstantRefundCapable,
    )

    assert not issubclass(GooglePayBuilder, AuthorizeCaptureCapable)
    assert not issubclass(GooglePayBuilder, BankTransferCapabilities)
    assert not issubclass(GooglePayBuilder, EncryptedPayCapable)
    assert not issubclass(GooglePayBuilder, FastCheckoutCapable)
    assert not issubclass(GooglePayBuilder, InstantRefundCapable)


def test_pay_dispatches_googlepay_service_through_mock_buckaroo():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "GP-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(GooglePayBuilder(client), amount=10.50)

    response = builder.pay(validate=False)

    assert response.key == "GP-1"
    mock.assert_all_consumed()
