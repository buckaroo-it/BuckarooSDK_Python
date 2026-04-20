"""Unit coverage for :class:`WeChatPayBuilder`.

Phase 7.37 — per-builder coverage. WeChatPayBuilder is a minimal subclass of
:class:`PaymentBuilder`: it overrides :meth:`get_service_name` and
:meth:`get_allowed_service_parameters` only, mixes in no capability classes,
and declares no ``_serviceName`` class attribute. Tests pin the public
surface, the allowed-parameter shape for every action we care about, and
end-to-end ``pay()`` via :class:`MockBuckaroo`.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.wechatpay_builder import WeChatPayBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# Construction


def test_construction_with_client_succeeds(client):
    builder = WeChatPayBuilder(client)

    assert isinstance(builder, WeChatPayBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_wechatpay_builder_does_not_declare_service_name_class_attribute():
    """WeChatPayBuilder relies on :meth:`get_service_name` — no ``_serviceName`` attr.

    Pin the current shape so a future refactor that introduces
    ``_serviceName`` has to update the assertion consciously.
    """
    assert "_serviceName" not in WeChatPayBuilder.__dict__


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_wechatpay(client):
    builder = WeChatPayBuilder(client)

    assert builder.get_service_name() == "WeChatPay"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every supported action


def test_get_allowed_service_parameters_pay_returns_empty_dict(client):
    builder = WeChatPayBuilder(client)

    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    """The builder lowercases the action name before matching."""
    builder = WeChatPayBuilder(client)

    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize(
    "action",
    ["Refund", "Capture", "Authorize", "UnknownAction"],
)
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    """Covers the fall-through ``return {}`` branch for any non-pay action."""
    builder = WeChatPayBuilder(client)

    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay_and_returns_empty(client):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    builder = WeChatPayBuilder(client)

    assert builder.get_allowed_service_parameters() == {}


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_wechatpay_service_to_transaction_endpoint_and_parses_response():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "WCP-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(WeChatPayBuilder(client), amount=12.34)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "WeChatPay"
    assert service["Action"] == "Pay"
    assert response.key == "WCP-1"
    mock.assert_all_consumed()
