"""Unit coverage for :class:`BlikBuilder`.

Blik is a minimal payment builder: no capability mixins, empty allowed-service-
parameter map, ``"Blik"`` service name. These tests pin that surface and drive
a single ``pay()`` round-trip through :class:`MockBuckaroo` for end-to-end
coverage of the builder's inherited action path.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.blik_builder import BlikBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def builder(client: BuckarooClient) -> BlikBuilder:
    return BlikBuilder(client)


def test_instantiates_as_payment_builder(builder: BlikBuilder) -> None:
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_blik(builder: BlikBuilder) -> None:
    assert builder.get_service_name() == "Blik"


def test_get_allowed_service_parameters_pay_is_empty_dict(
    builder: BlikBuilder,
) -> None:
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_default_action_matches_pay(
    builder: BlikBuilder,
) -> None:
    # The ``action`` parameter defaults to ``"Pay"``; snapshot the default branch.
    assert builder.get_allowed_service_parameters() == {}


def test_get_allowed_service_parameters_other_actions_also_empty(
    builder: BlikBuilder,
) -> None:
    # BlikBuilder returns an empty dict unconditionally — snapshot non-Pay actions
    # so a future per-action table doesn't silently regress the Blik contract.
    for action in ("Refund", "Authorize", "Capture"):
        assert builder.get_allowed_service_parameters(action) == {}


def test_does_not_mix_in_capability_only_methods(builder: BlikBuilder) -> None:
    # Capability mixins are opt-in. Blik opts out; none of the capability-only
    # methods (i.e. methods that *only* exist on a mixin, not on the base) should
    # appear on the builder. ``capture`` is inherited from ``BaseBuilder`` and
    # deliberately excluded from this list.
    for method in (
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
        "payEncrypted",
        "instantRefund",
        "payFastCheckout",
    ):
        assert not hasattr(builder, method), (
            f"BlikBuilder unexpectedly exposes capability method {method!r}"
        )


def test_pay_posts_transaction_through_mock_strategy(
    builder: BlikBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "blik-key", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = populate_required_fields(
        builder,
        currency="PLN",
        description="Blik payment",
        invoice="INV-BLIK-1",
        return_url="https://example.test/return",
        return_url_cancel="https://example.test/cancel",
        return_url_error="https://example.test/error",
        return_url_reject="https://example.test/reject",
    ).pay()

    assert response.key == "blik-key"
    assert response.status.code.code == 190
    mock_strategy.assert_all_consumed()
