"""Unit tests for :class:`DefaultBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/default_builder.py``. The builder is a catch-all
that unknown-method lookups fall back to. It declares no capability mixins,
no ``_serviceName`` class attribute, and no action methods of its own. The
surface under test is:

- construction via ``BuckarooClient`` wired to :class:`MockBuckaroo`
- ``get_service_name()`` reading ``method`` from the payload (and falling
  back to ``"Unknown"`` when absent)
- ``get_allowed_service_parameters(action)`` returning ``{}`` for every
  action — the catch-all has no required params
- ``pay()`` end-to-end through the mock strategy
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.default_builder import DefaultBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


def test_construction_with_client_succeeds(client):
    builder = DefaultBuilder(client)
    assert isinstance(builder, DefaultBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_defaults_to_unknown_when_payload_has_no_method(client):
    assert DefaultBuilder(client).get_service_name() == "Unknown"


def test_get_service_name_reads_method_from_payload(client):
    builder = DefaultBuilder(client)
    builder.from_dict({"method": "someobscuremethod"})
    assert builder.get_service_name() == "someobscuremethod"


def test_get_allowed_service_parameters_pay_snapshot(client):
    """Catch-all: no required (or optional) params for any action."""
    assert DefaultBuilder(client).get_allowed_service_parameters("Pay") == {}


@pytest.mark.parametrize(
    "action",
    ["Pay", "pay", "Refund", "Capture", "Authorize", "UnknownAction", ""],
)
def test_get_allowed_service_parameters_any_action_returns_empty(client, action):
    assert DefaultBuilder(client).get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_default_action_returns_empty(client):
    """Exercises the ``action="Pay"`` default argument."""
    assert DefaultBuilder(client).get_allowed_service_parameters() == {}


@pytest.mark.parametrize(
    "mixin_method",
    [
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
        "payEncrypted",
        "instantRefund",
        "payFastCheckout",
    ],
)
def test_has_no_capability_mixin_methods(client, mixin_method):
    """DefaultBuilder mixes in no capabilities — the mixin methods are absent."""
    assert not hasattr(DefaultBuilder(client), mixin_method), (
        f"DefaultBuilder unexpectedly exposes capability method {mixin_method!r}"
    )


def test_inherits_base_builder_action_methods(client):
    """BaseBuilder-defined action methods (not mixins) are present and callable."""
    builder = DefaultBuilder(client)
    for method in ("pay", "refund", "capture", "cancel", "partial_refund", "execute_action"):
        assert hasattr(builder, method)
        assert callable(getattr(builder, method))


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "default-key-42", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(DefaultBuilder(client))
        .pay()
    )

    assert response.key == "default-key-42"
    mock_strategy.assert_all_consumed()


def test_pay_uses_method_from_payload_as_service_name(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "default-key-99"},
        )
    )

    response = DefaultBuilder(client).from_dict(TestHelpers.standard_payload(
        invoice="INV-DEF-2",
        amount=5.55,
        description="via from_dict",
        method="obscuremethod",
    )).pay()

    assert response.key == "default-key-99"
    mock_strategy.assert_all_consumed()
