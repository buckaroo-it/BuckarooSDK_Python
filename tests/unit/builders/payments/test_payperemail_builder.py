"""Unit coverage for :class:`PayPerEmailBuilder`.

Pay Per Email drives the ``PaymentInvitation`` action: Buckaroo emails the
shopper a payment link instead of returning an inline redirect. The builder
carries no capability mixins and exposes its parameter spec only for the
``PaymentInvitation`` action (``Pay`` is empty). The per-action spec and an
end-to-end ``execute_action("PaymentInvitation")`` via :class:`RecordingMock`
are pinned inline so drift is loud.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.payperemail_builder import PayPerEmailBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import RecordingMock, recorded_action, recorded_service_parameters


@pytest.fixture
def builder(client: BuckarooClient) -> PayPerEmailBuilder:
    return PayPerEmailBuilder(client)


def test_builder_instantiates_as_payment_builder(builder: PayPerEmailBuilder) -> None:
    assert isinstance(builder, PayPerEmailBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_service_name_is_payperemail(builder: PayPerEmailBuilder) -> None:
    assert builder.get_service_name() == "payperemail"
    assert PayPerEmailBuilder._serviceName == "payperemail"


_PAYMENT_INVITATION_SPEC = {
    "CustomerGender": {
        "type": (str, int),
        "required": True,
        "description": "Customer gender (1=Male, 2=Female, 0=Unknown, 9=N/A)",
    },
    "CustomerEmail": {"type": str, "required": True, "description": "Customer email address"},
    "CustomerFirstName": {"type": str, "required": True, "description": "Customer first name"},
    "CustomerLastName": {"type": str, "required": True, "description": "Customer last name"},
    "ExpirationDate": {
        "type": str,
        "required": False,
        "description": "Invitation expiration date",
    },
    "PaymentMethodsAllowed": {
        "type": str,
        "required": False,
        "description": "Allowed payment methods (CSV)",
    },
    "MerchantSendsEmail": {
        "type": (str, bool),
        "required": False,
        "description": "Whether the merchant sends the email instead of Buckaroo",
    },
}


def test_get_allowed_service_parameters_payment_invitation_snapshot(
    builder: PayPerEmailBuilder,
) -> None:
    assert builder.get_allowed_service_parameters("PaymentInvitation") == _PAYMENT_INVITATION_SPEC


def test_get_allowed_service_parameters_payment_invitation_case_insensitive(
    builder: PayPerEmailBuilder,
) -> None:
    # Source lowercases the action before comparing.
    assert builder.get_allowed_service_parameters(
        "paymentinvitation"
    ) == builder.get_allowed_service_parameters("PaymentInvitation")


@pytest.mark.parametrize("action", ["Pay", "Refund", "Authorize", "Capture", ""])
def test_get_allowed_service_parameters_other_actions_return_empty(
    builder: PayPerEmailBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


def test_payment_invitation_end_to_end_uses_invitation_action(
    builder: PayPerEmailBuilder,
) -> None:
    """``execute_action("PaymentInvitation")`` posts the invitation action with
    the customer params on the wire — not a plain Pay."""
    mock = RecordingMock()
    builder._client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "ppe-key", "Status": {"Code": {"Code": 791}}},
        )
    )

    response = (
        builder.currency("EUR")
        .amount(42.00)
        .description("PPE invite")
        .invoice("INV-PPE-1")
        .return_url("https://ret.example/ok")
        .return_url_cancel("https://ret.example/cancel")
        .return_url_error("https://ret.example/error")
        .return_url_reject("https://ret.example/reject")
        .from_dict(
            {
                "service_parameters": {
                    "CustomerEmail": "jane@example.com",
                    "CustomerFirstName": "Jane",
                    "CustomerLastName": "Doe",
                    "CustomerGender": "1",
                }
            }
        )
        .execute_action("PaymentInvitation")
    )

    assert response.key == "ppe-key"
    assert recorded_action(mock) == "PaymentInvitation"
    sent = {p["Name"].lower(): p["Value"] for p in recorded_service_parameters(mock)}
    assert sent["customeremail"] == "jane@example.com"
    assert sent["customerfirstname"] == "Jane"
    assert sent["customerlastname"] == "Doe"
    assert sent["customergender"] == "1"
