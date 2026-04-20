"""Unit coverage for :class:`TwintBuilder`.

Twint is a minimal payment builder: no capability mixins, empty allowed-service-
parameter map for ``Pay``, ``"Twint"`` service name. These tests pin that
surface and drive a single ``pay()`` round-trip through :class:`MockBuckaroo`
for end-to-end coverage of the inherited action path.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.twint_builder import TwintBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def builder(client: BuckarooClient) -> TwintBuilder:
    return TwintBuilder(client)


def test_instantiates_as_payment_builder(builder: TwintBuilder) -> None:
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_twint(builder: TwintBuilder) -> None:
    assert builder.get_service_name() == "Twint"


def test_get_allowed_service_parameters_pay_is_empty_dict(
    builder: TwintBuilder,
) -> None:
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_default_action_matches_pay(
    builder: TwintBuilder,
) -> None:
    # The ``action`` parameter defaults to ``"Pay"``; snapshot the default
    # branch so a future override can't silently drift from explicit ``"Pay"``.
    assert builder.get_allowed_service_parameters() == {}


def test_get_allowed_service_parameters_pay_is_case_insensitive(
    builder: TwintBuilder,
) -> None:
    # ``action.lower() in ["pay"]`` branch — confirm lowercase matches.
    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize("action", ["Refund", "Authorize", "Capture", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(
    builder: TwintBuilder, action: str
) -> None:
    # Exercises the fall-through ``return {}`` branch.
    assert builder.get_allowed_service_parameters(action) == {}


def test_has_inherited_pay_action_method(builder: TwintBuilder) -> None:
    # Twint mixes in no capability classes; only the inherited ``pay`` action
    # is available. Pin presence + callability so a refactor of the base class
    # that hides ``pay`` surfaces here.
    assert hasattr(builder, "pay")
    assert callable(builder.pay)


def test_does_not_mix_in_capability_only_methods(builder: TwintBuilder) -> None:
    # Despite the docstring referencing "bank transfer capabilities", the
    # class body opts out of every capability mixin. Pin that none of the
    # capability-only methods leak onto the builder.
    for method in (
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
        "payEncrypted",
        "instantRefund",
        "payFastCheckout",
    ):
        assert not hasattr(builder, method), (
            f"TwintBuilder unexpectedly exposes capability method {method!r}"
        )


def test_pay_posts_transaction_through_mock_strategy(
    builder: TwintBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "twint-key", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = populate_required_fields(
        builder,
        currency="CHF",
        amount=25.5,
        description="Twint payment",
        invoice="INV-TWINT-1",
        return_url="https://example.test/return",
        return_url_cancel="https://example.test/cancel",
        return_url_error="https://example.test/error",
        return_url_reject="https://example.test/reject",
    ).pay()

    assert response.key == "twint-key"
    assert response.status.code.code == 190
    mock_strategy.assert_all_consumed()
