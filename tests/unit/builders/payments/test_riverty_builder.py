"""Unit coverage for :class:`RivertyBuilder`.

Riverty is a buy-now-pay-later method (formerly AfterPay). The builder
mixes in :class:`AuthorizeCaptureCapable` for authorize/capture/void, and
exposes a cart-line-item oriented parameter spec shared between ``Pay``
and ``Authorize``. Per-action spec and end-to-end ``pay()`` /
``authorize()`` via :class:`MockBuckaroo` are pinned inline so drift is loud.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
    AuthorizeCaptureCapable,
)
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.riverty_builder import RivertyBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client: BuckarooClient) -> RivertyBuilder:
    return RivertyBuilder(client)


def test_builder_instantiates_as_payment_builder(builder: RivertyBuilder) -> None:
    assert isinstance(builder, RivertyBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_builder_mixes_in_authorize_capture_capable(builder: RivertyBuilder) -> None:
    assert isinstance(builder, AuthorizeCaptureCapable)


def test_get_service_name_returns_afterpay(builder: RivertyBuilder) -> None:
    # Riverty is the rebrand of AfterPay; Buckaroo's API still uses the
    # ``afterpay`` service name on the wire.
    assert builder.get_service_name() == "afterpay"


_PAY_AUTHORIZE_SPEC = {
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


def test_get_allowed_service_parameters_pay_snapshot(builder: RivertyBuilder) -> None:
    assert builder.get_allowed_service_parameters("Pay") == _PAY_AUTHORIZE_SPEC


def test_get_allowed_service_parameters_authorize_matches_pay(builder: RivertyBuilder) -> None:
    """Authorize uses the same cart trio as Pay — same billingCustomer,
    shippingCustomer, and article requirements."""
    assert builder.get_allowed_service_parameters("Authorize") == _PAY_AUTHORIZE_SPEC


def test_get_allowed_service_parameters_pay_case_insensitive(
    builder: RivertyBuilder,
) -> None:
    # Source lowercases the action before comparing.
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )
    assert builder.get_allowed_service_parameters("PAY") == builder.get_allowed_service_parameters(
        "Pay"
    )
    assert builder.get_allowed_service_parameters(
        "authorize"
    ) == builder.get_allowed_service_parameters("Authorize")


@pytest.mark.parametrize("action", ["Refund", "Capture", "CancelAuthorize", ""])
def test_get_allowed_service_parameters_non_cart_actions_return_empty(
    builder: RivertyBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay(builder: RivertyBuilder) -> None:
    # Default ``action`` arg is ``"Pay"`` — no-arg call must match the Pay spec.
    assert builder.get_allowed_service_parameters() == builder.get_allowed_service_parameters("Pay")


def test_pay_end_to_end_via_mock_buckaroo(
    builder: RivertyBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "riverty-key", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(builder, amount=79.50)
        .from_dict(
            {
                "service_parameters": {
                    "billingCustomer": {"firstName": "Jane", "lastName": "Doe"},
                    "shippingCustomer": {"firstName": "Jane", "lastName": "Doe"},
                    "article": [
                        {
                            "identifier": "SKU-1",
                            "description": "Widget",
                            "quantity": 1,
                            "price": 79.50,
                        },
                    ],
                }
            }
        )
        .pay()
    )

    assert response.key == "riverty-key"


def test_authorize_end_to_end_via_mock_buckaroo(
    builder: RivertyBuilder, mock_strategy: MockBuckaroo
) -> None:
    """Authorize round-trips through the full stack and uses the cart trio.
    Pinned to surface a regression if the Authorize action plumbing breaks."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "riverty-auth-key", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(builder, amount=79.50)
        .from_dict(
            {
                "service_parameters": {
                    "billingCustomer": {"firstName": "Jane", "lastName": "Doe"},
                    "shippingCustomer": {"firstName": "Jane", "lastName": "Doe"},
                    "article": [
                        {
                            "identifier": "SKU-1",
                            "description": "Widget",
                            "quantity": 1,
                            "price": 79.50,
                        },
                    ],
                }
            }
        )
        .authorize()
    )

    assert response.key == "riverty-auth-key"


def test_cancel_authorize_requires_original_transaction_key(client: BuckarooClient) -> None:
    """Missing key raises ValueError — same contract as creditcard."""
    builder = populate_required_fields(RivertyBuilder(client), amount=10.0)
    with pytest.raises(ValueError, match="Original transaction key is required"):
        builder.cancelAuthorize(original_transaction_key="")
