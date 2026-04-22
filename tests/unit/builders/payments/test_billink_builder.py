"""Unit coverage for :class:`BillinkBuilder`.

Billink is a buy-now-pay-later method. The builder has no capability mixins
and exposes a single cart-line-item oriented parameter spec for ``Pay``.
Per-action spec and end-to-end ``pay()`` via :class:`MockBuckaroo` are pinned
inline so drift is loud.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.billink_builder import BillinkBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client: BuckarooClient) -> BillinkBuilder:
    return BillinkBuilder(client)


def test_builder_instantiates_as_payment_builder(builder: BillinkBuilder) -> None:
    assert isinstance(builder, BillinkBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_billink(builder: BillinkBuilder) -> None:
    assert builder.get_service_name() == "billink"


def test_get_allowed_service_parameters_pay_snapshot(builder: BillinkBuilder) -> None:
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
            "description": "Billink articles",
        },
    }


def test_get_allowed_service_parameters_pay_case_insensitive(
    builder: BillinkBuilder,
) -> None:
    # Source lowercases the action before comparing.
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )
    assert builder.get_allowed_service_parameters("PAY") == builder.get_allowed_service_parameters(
        "Pay"
    )


@pytest.mark.parametrize("action", ["Refund", "Authorize", "Capture", "CancelAuthorize", ""])
def test_get_allowed_service_parameters_non_pay_actions_return_empty(
    builder: BillinkBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


def test_pay_end_to_end_via_mock_buckaroo(
    builder: BillinkBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "billink-key", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(builder, amount=49.95)
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
                            "price": 49.95,
                        },
                    ],
                }
            }
        )
        .pay()
    )

    assert response.key == "billink-key"
    assert response.status.code.code == 190
