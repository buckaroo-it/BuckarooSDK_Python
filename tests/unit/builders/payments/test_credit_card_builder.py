"""Tests for :class:`buckaroo.builders.payments.credit_card_builder.CreditcardBuilder`.

Covers the three quirks specific to this builder:

- Dynamic :meth:`get_service_name` — reads ``brand`` off ``_payload`` and
  defaults to ``"CreditCard"`` when absent.
- The per-action allowed-parameters matrix for ``Pay``, ``PayEncrypted``,
  ``PayWithSecurityCode``, ``PayWithToken``, ``PayRecurrent``, ``Authorize``,
  ``AuthorizeWithToken``, ``Capture`` and ``Refund``.
- The four builder-specific actions: ``payWithSecurityCode``, ``payWithToken``,
  ``authorizeWithToken`` and ``payRecurrent``. Each is exercised end-to-end
  through a :class:`BuckarooClient` wired to :class:`MockBuckaroo`.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
    AuthorizeCaptureCapable,
)
from buckaroo.builders.payments.capabilities.encrypted_pay_capable import (
    EncryptedPayCapable,
)
from buckaroo.builders.payments.credit_card_builder import CreditcardBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, wire_recording_http


# ---------------------------------------------------------------------------
# Fixtures


@pytest.fixture
def client():
    """BuckarooClient wired to a non-recording MockBuckaroo strategy."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = MockBuckaroo()
    return c


# ---------------------------------------------------------------------------
# Construction + source constants


class TestConstruction:
    def test_instantiates_with_buckaroo_client(self, client):
        builder = CreditcardBuilder(client)
        assert isinstance(builder, CreditcardBuilder)
        assert isinstance(builder, PaymentBuilder)

    def test_service_name_class_constant_is_creditcard(self):
        assert CreditcardBuilder._serviceName == "creditcard"

    def test_is_encrypted_pay_capable(self):
        assert issubclass(CreditcardBuilder, EncryptedPayCapable)

    def test_is_authorize_capture_capable(self):
        assert issubclass(CreditcardBuilder, AuthorizeCaptureCapable)


# ---------------------------------------------------------------------------
# Dynamic get_service_name()


class TestGetServiceName:
    def test_returns_CreditCard_when_payload_has_no_brand(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_service_name() == "CreditCard"

    def test_returns_brand_from_payload_when_present(self, client):
        builder = CreditcardBuilder(client)
        builder.from_dict({"brand": "Visa"})
        assert builder.get_service_name() == "Visa"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — full action matrix


class TestGetAllowedServiceParameters:
    def test_pay_returns_empty_dict(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("Pay") == {}

    def test_pay_encrypted_returns_encryptedcarddata_spec(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("PayEncrypted") == {
            "encryptedcarddata": {
                "type": str,
                "required": True,
                "description": "Encrypted card data",
            },
        }

    def test_pay_with_security_code_returns_encryptedsecuritycode_spec(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("PayWithSecurityCode") == {
            "encryptedsecuritycode": {
                "type": str,
                "required": True,
                "description": "Encrypted security code",
            },
        }

    def test_pay_with_token_returns_sessionid_spec(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("PayWithToken") == {
            "sessionid": {
                "type": str,
                "required": True,
                "description": "Session ID token from Hosted Fields submitSession()",
            },
        }

    def test_authorize_with_token_returns_sessionid_spec(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("AuthorizeWithToken") == {
            "sessionid": {
                "type": str,
                "required": True,
                "description": "Session ID token from Hosted Fields submitSession()",
            },
        }

    def test_pay_recurrent_returns_empty_dict(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("PayRecurrent") == {}

    def test_authorize_returns_empty_dict(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("Authorize") == {}

    def test_capture_returns_empty_dict(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("Capture") == {}

    def test_refund_returns_empty_dict(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("Refund") == {}

    def test_defaults_to_pay_when_action_omitted(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters() == {}

    def test_unknown_action_returns_empty_dict(self, client):
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("Completely-Unknown") == {}

    def test_action_matching_is_case_insensitive(self, client):
        """The source lowercases ``action`` before each branch comparison."""
        builder = CreditcardBuilder(client)
        assert builder.get_allowed_service_parameters("payencrypted") == {
            "encryptedcarddata": {
                "type": str,
                "required": True,
                "description": "Encrypted card data",
            },
        }


# ---------------------------------------------------------------------------
# Capability-mixin sanity — methods from mixins are present and callable


class TestCapabilityMixinMethods:
    def test_pay_encrypted_present_and_callable(self, client):
        builder = CreditcardBuilder(client)
        assert hasattr(builder, "payEncrypted")
        assert callable(builder.payEncrypted)

    def test_authorize_present_and_callable(self, client):
        builder = CreditcardBuilder(client)
        assert hasattr(builder, "authorize")
        assert callable(builder.authorize)

    def test_authorize_encrypted_present_and_callable(self, client):
        builder = CreditcardBuilder(client)
        assert hasattr(builder, "authorizeEncrypted")
        assert callable(builder.authorizeEncrypted)

    def test_capture_present_and_callable(self, client):
        builder = CreditcardBuilder(client)
        assert hasattr(builder, "capture")
        assert callable(builder.capture)

    def test_cancel_authorize_present_and_callable(self, client):
        builder = CreditcardBuilder(client)
        assert hasattr(builder, "cancelAuthorize")
        assert callable(builder.cancelAuthorize)


# ---------------------------------------------------------------------------
# Builder-specific action methods — end-to-end through MockBuckaroo


def _ready_builder(client):
    builder = CreditcardBuilder(client)
    populate_required_fields(builder, amount=10.50)
    return builder


class TestPayWithSecurityCode:
    def test_posts_action_PayWithSecurityCode_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "PSC-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.payWithSecurityCode(validate=False)

        assert recorded_action(mock) == "PayWithSecurityCode"
        assert response.key == "PSC-1"
        mock.assert_all_consumed()


class TestPayWithToken:
    def test_posts_action_PayWithToken_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "PWT-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.payWithToken(validate=False)

        assert recorded_action(mock) == "PayWithToken"
        assert response.key == "PWT-1"
        mock.assert_all_consumed()


class TestAuthorizeWithToken:
    def test_posts_action_AuthorizeWithToken_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "AWT-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.authorizeWithToken(validate=False)

        assert recorded_action(mock) == "AuthorizeWithToken"
        assert response.key == "AWT-1"
        mock.assert_all_consumed()


class TestPayRecurrent:
    def test_posts_action_PayRecurrent_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "PR-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.payRecurrent(validate=False)

        assert recorded_action(mock) == "PayRecurrent"
        assert response.key == "PR-1"
        mock.assert_all_consumed()
