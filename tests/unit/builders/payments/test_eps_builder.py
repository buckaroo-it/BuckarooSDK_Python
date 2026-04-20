"""Per-builder unit tests for :class:`EpsBuilder`.

EPS is a trivial builder: no capability mixins, no builder-specific action
methods, and ``get_allowed_service_parameters`` returns an empty dict for
every action. Tests pin those contracts and exercise ``pay()`` end-to-end
through :class:`tests.support.mock_buckaroo.MockBuckaroo`.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.eps_builder import EpsBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client: BuckarooClient) -> EpsBuilder:
    return EpsBuilder(client)


def test_construction_yields_payment_builder_subclass(builder: EpsBuilder) -> None:
    assert isinstance(builder, EpsBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_eps(builder: EpsBuilder) -> None:
    assert builder.get_service_name() == "EPS"


@pytest.mark.parametrize("action", ["Pay", "Refund", "Authorize", "Capture"])
def test_get_allowed_service_parameters_is_empty_for_every_action(
    builder: EpsBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay(builder: EpsBuilder) -> None:
    assert builder.get_allowed_service_parameters() == {}


def test_pay_posts_eps_action_and_parses_response(
    builder: EpsBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "eps-txn-key",
                "Status": {"Code": {"Code": 190}},
                "Services": [{"Name": "EPS", "Action": "Pay"}],
            },
        )
    )

    response = (
        populate_required_fields(builder, amount=12.34)
        .pay()
    )

    assert response.key == "eps-txn-key"
    assert response.services[0].name == "EPS"
    assert response.services[0].action == "Pay"
    mock_strategy.assert_all_consumed()
