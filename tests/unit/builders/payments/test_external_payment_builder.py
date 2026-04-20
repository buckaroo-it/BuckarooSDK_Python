"""Unit coverage for :class:`ExternalPaymentBuilder`.

The External payment method is a pass-through: it declares no service-level
parameters and inherits every action method from :class:`PaymentBuilder` /
:class:`BaseBuilder`. These tests pin that shape and round-trip a ``pay()``
and ``refund()`` through :class:`MockBuckaroo` so regressions in the inherited
plumbing surface here too.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
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
from buckaroo.builders.payments.external_payment_builder import ExternalPaymentBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.models.payment_response import PaymentResponse
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


@pytest.fixture
def builder(client: BuckarooClient) -> ExternalPaymentBuilder:
    return ExternalPaymentBuilder(client)


def test_instantiates_as_payment_builder(builder: ExternalPaymentBuilder) -> None:
    assert isinstance(builder, PaymentBuilder)


def test_does_not_declare_class_level_service_name() -> None:
    # ExternalPayment resolves the service name at call time via
    # get_service_name(); no class-level _serviceName attribute is declared.
    assert "_serviceName" not in vars(ExternalPaymentBuilder)


def test_get_service_name_returns_external_payment(
    builder: ExternalPaymentBuilder,
) -> None:
    assert builder.get_service_name() == "ExternalPayment"


@pytest.mark.parametrize(
    "action",
    ["Pay", "Refund", "Capture", "PayRemainder", "Authorize", ""],
)
def test_get_allowed_service_parameters_is_empty_for_every_action(
    builder: ExternalPaymentBuilder, action: str
) -> None:
    # Pass-through builder: no service-level parameters declared, regardless
    # of the action supplied. Snapshot the declared spec inline as {}.
    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay(
    builder: ExternalPaymentBuilder,
) -> None:
    assert builder.get_allowed_service_parameters() == {}


@pytest.mark.parametrize(
    "capability",
    [
        AuthorizeCaptureCapable,
        BankTransferCapabilities,
        EncryptedPayCapable,
        FastCheckoutCapable,
        InstantRefundCapable,
    ],
)
def test_does_not_mix_in_any_capability(capability: type) -> None:
    assert not issubclass(ExternalPaymentBuilder, capability)


@pytest.mark.parametrize(
    "method_name", ["pay", "refund", "capture", "cancel", "execute_action", "build"]
)
def test_base_builder_methods_are_present_and_callable(
    builder: ExternalPaymentBuilder, method_name: str
) -> None:
    assert hasattr(builder, method_name)
    assert callable(getattr(builder, method_name))


def test_pay_round_trips_through_mock_buckaroo(
    builder: ExternalPaymentBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "EXT-TXN-1",
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
                "Services": [
                    {"Name": "ExternalPayment", "Action": "Pay", "Parameters": []}
                ],
                "Invoice": "INV-EXT-001",
                "Currency": "EUR",
                "AmountDebit": 25.0,
            },
        )
    )

    response = builder.from_dict(TestHelpers.standard_payload(
        invoice="INV-EXT-001",
        amount=25.0,
        description="External pay",
    )).pay()

    assert isinstance(response, PaymentResponse)
    assert response.key == "EXT-TXN-1"
    assert response.status.code.code == 190
    mock_strategy.assert_all_consumed()


def test_refund_round_trips_through_mock_buckaroo(
    builder: ExternalPaymentBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "EXT-REFUND-1",
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
                "Services": [
                    {"Name": "ExternalPayment", "Action": "Refund", "Parameters": []}
                ],
                "Invoice": "INV-EXT-REFUND",
                "Currency": "EUR",
                "AmountCredit": 10.0,
            },
        )
    )

    response = builder.from_dict(TestHelpers.standard_payload(
        invoice="INV-EXT-REFUND",
        amount=10.0,
        description="External refund",
        original_transaction_key="ORIG-EXT-KEY",
    )).refund()

    assert isinstance(response, PaymentResponse)
    assert response.key == "EXT-REFUND-1"
    assert response.status.code.code == 190
    mock_strategy.assert_all_consumed()
