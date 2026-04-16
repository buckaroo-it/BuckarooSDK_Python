"""Per-builder unit tests for :class:`ClickToPayBuilder`.

Covers the trivial per-builder surface: construction, service name, allowed
service parameters per action, capability sanity, and one end-to-end ``pay()``
round-trip through :class:`MockBuckaroo`.

``ClickToPayBuilder`` doesn't declare a ``_serviceName`` class attribute (unlike
:class:`CreditcardBuilder`); the authoritative service name is exposed via
``get_service_name()`` and is what gets asserted here.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.click_to_pay_builder import ClickToPayBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def mock_buckaroo():
    return MockBuckaroo()


@pytest.fixture
def client(mock_buckaroo):
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_buckaroo
    return c


@pytest.fixture
def builder(client):
    return ClickToPayBuilder(client)


def test_construction_returns_payment_builder(builder):
    assert isinstance(builder, PaymentBuilder)
    assert isinstance(builder, ClickToPayBuilder)


def test_get_service_name_returns_click_to_pay(builder):
    assert builder.get_service_name() == "ClickToPay"


def test_get_allowed_service_parameters_pay_is_empty(builder):
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_defaults_to_pay(builder):
    assert builder.get_allowed_service_parameters() == {}


def test_get_allowed_service_parameters_unknown_action_is_empty(builder):
    assert builder.get_allowed_service_parameters("Refund") == {}


def test_no_capability_mixins_declared(builder):
    """ClickToPayBuilder has no capability mixins — only the base methods."""
    from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
        AuthorizeCaptureCapable,
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

    assert not isinstance(builder, AuthorizeCaptureCapable)
    assert not isinstance(builder, EncryptedPayCapable)
    assert not isinstance(builder, FastCheckoutCapable)
    assert not isinstance(builder, InstantRefundCapable)


def test_base_pay_method_present_and_callable(builder):
    assert hasattr(builder, "pay")
    assert callable(builder.pay)


def test_pay_end_to_end_through_mock_buckaroo(builder, mock_buckaroo):
    """pay() builds a Pay action against the ClickToPay service, sends it
    through the HTTP client, and returns a parsed PaymentResponse."""
    mock_buckaroo.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "CTP-KEY",
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
                "Services": [{"Name": "ClickToPay", "Action": "Pay"}],
            },
        )
    )

    response = (
        builder.currency("EUR")
        .amount(12.34)
        .description("desc")
        .invoice("INV-CTP-1")
        .return_url("https://ret.example/ok")
        .return_url_cancel("https://ret.example/cancel")
        .return_url_error("https://ret.example/error")
        .return_url_reject("https://ret.example/reject")
        .pay()
    )

    assert response.key == "CTP-KEY"
    assert response.status.code.code == 190
    mock_buckaroo.assert_all_consumed()
