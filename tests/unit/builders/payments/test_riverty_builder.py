"""Unit coverage for :class:`RivertyBuilder`.

Riverty is a buy-now-pay-later method (formerly AfterPay). The builder has
no capability mixins and exposes a single cart-line-item oriented parameter
spec for ``Pay``. Per-action spec and end-to-end ``pay()`` via
:class:`MockBuckaroo` are pinned inline so drift is loud.
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
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.riverty_builder import RivertyBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def mock_buckaroo() -> MockBuckaroo:
    return MockBuckaroo()


@pytest.fixture
def client(mock_buckaroo: MockBuckaroo) -> BuckarooClient:
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_buckaroo
    return c


@pytest.fixture
def builder(client: BuckarooClient) -> RivertyBuilder:
    return RivertyBuilder(client)


def test_builder_instantiates_as_payment_builder(builder: RivertyBuilder) -> None:
    assert isinstance(builder, RivertyBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_afterpay(builder: RivertyBuilder) -> None:
    # Riverty is the rebrand of AfterPay; Buckaroo's API still uses the
    # ``afterpay`` service name on the wire.
    assert builder.get_service_name() == "afterpay"


def test_get_allowed_service_parameters_pay_snapshot(builder: RivertyBuilder) -> None:
    assert builder.get_allowed_service_parameters("Pay") == {
        "billingCustomer": {
            "type": list,
            "required": True,
            "description": "Billing customer information",
        },
        "shippingCustomer": {
            "type": list,
            "required": True,
            "description": "Shipping customer information",
        },
        "article": {
            "type": list,
            "required": True,
            "description": "Riverty articles",
        },
    }


def test_get_allowed_service_parameters_pay_case_insensitive(
    builder: RivertyBuilder,
) -> None:
    # Source lowercases the action before comparing.
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters("Pay")
    assert builder.get_allowed_service_parameters("PAY") == builder.get_allowed_service_parameters("Pay")


@pytest.mark.parametrize("action", ["Refund", "Authorize", "Capture", "CancelAuthorize", ""])
def test_get_allowed_service_parameters_non_pay_actions_return_empty(
    builder: RivertyBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay(builder: RivertyBuilder) -> None:
    # Default ``action`` arg is ``"Pay"`` — no-arg call must match the Pay spec.
    assert builder.get_allowed_service_parameters() == builder.get_allowed_service_parameters("Pay")


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
def test_builder_does_not_mix_in_capability(
    builder: RivertyBuilder, capability: type
) -> None:
    # Riverty ships no capability mixins — pin the MRO so a future mixin
    # addition lands with a visible test change.
    assert not isinstance(builder, capability)


def test_inherited_payment_actions_are_callable(builder: RivertyBuilder) -> None:
    # BaseBuilder provides these; pin that RivertyBuilder exposes them through
    # inheritance so callers can rely on the public API shape.
    for method_name in ("pay", "refund", "capture", "cancel", "partial_refund", "execute_action"):
        assert hasattr(builder, method_name)
        assert callable(getattr(builder, method_name))


def test_pay_end_to_end_via_mock_buckaroo(
    builder: RivertyBuilder, mock_buckaroo: MockBuckaroo
) -> None:
    mock_buckaroo.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "riverty-key", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        builder.currency("EUR")
        .amount(79.50)
        .description("Riverty order")
        .invoice("INV-RIVERTY-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .from_dict(
            {
                "service_parameters": {
                    "billingCustomer": {"firstName": "Jane", "lastName": "Doe"},
                    "shippingCustomer": {"firstName": "Jane", "lastName": "Doe"},
                    "article": [
                        {"identifier": "SKU-1", "description": "Widget", "quantity": 1, "price": 79.50},
                    ],
                }
            }
        )
        .pay()
    )

    assert response.key == "riverty-key"
    mock_buckaroo.assert_all_consumed()
