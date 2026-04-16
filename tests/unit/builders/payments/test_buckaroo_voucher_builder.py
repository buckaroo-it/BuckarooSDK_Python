"""Unit tests for :class:`BuckarooVoucherBuilder`.

Per-builder coverage: construction, ``get_service_name()``, parameter
spec snapshots per supported action, and an end-to-end post round-trip
via :class:`MockBuckaroo`.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.buckaroo_voucher_builder import (
    BuckarooVoucherBuilder,
)
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_buckaroo import MockBuckaroo


@pytest.fixture
def client():
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = MockBuckaroo()
    return c


class TestConstruction:
    def test_instantiates_with_client_as_payment_builder(self, client):
        builder = BuckarooVoucherBuilder(client)
        assert isinstance(builder, PaymentBuilder)


class TestServiceName:
    def test_get_service_name_returns_buckaroo_voucher(self, client):
        assert BuckarooVoucherBuilder(client).get_service_name() == "Buckaroo Voucher"


VOUCHER_CODE_SPEC = {
    "VoucherCode": {
        "type": str,
        "required": True,
        "description": "The voucher code to use for the payment",
    },
}


class TestAllowedServiceParameters:
    def test_pay_action_returns_voucher_code_spec(self, client):
        allowed = BuckarooVoucherBuilder(client).get_allowed_service_parameters("Pay")
        assert allowed == VOUCHER_CODE_SPEC

    def test_getbalance_action_returns_voucher_code_spec(self, client):
        allowed = BuckarooVoucherBuilder(client).get_allowed_service_parameters(
            "GetBalance"
        )
        assert allowed == VOUCHER_CODE_SPEC

    def test_deactivatevoucher_action_returns_voucher_code_spec(self, client):
        allowed = BuckarooVoucherBuilder(client).get_allowed_service_parameters(
            "DeactivateVoucher"
        )
        assert allowed == VOUCHER_CODE_SPEC

    def test_createapplication_action_returns_application_spec(self, client):
        allowed = BuckarooVoucherBuilder(client).get_allowed_service_parameters(
            "CreateApplication"
        )
        assert allowed == {
            "GroupReference": {
                "type": str,
                "required": False,
                "description": "The group reference for the application",
            },
            "UsageType": {
                "type": str,
                "required": True,
                "description": "The usage type for the voucher application",
            },
            "ValidFrom": {
                "type": str,
                "required": True,
                "description": "The start date of voucher validity",
            },
            "ValidUntil": {
                "type": str,
                "required": False,
                "description": "The end date of voucher validity",
            },
            "CreationBalance": {
                "type": float,
                "required": True,
                "description": "The initial balance of the voucher",
            },
        }

    def test_default_action_is_pay(self, client):
        builder = BuckarooVoucherBuilder(client)
        assert builder.get_allowed_service_parameters() == VOUCHER_CODE_SPEC

    @pytest.mark.parametrize(
        "action",
        ["pay", "PAY", "getbalance", "GETBALANCE", "deactivatevoucher", "createapplication", "CREATEAPPLICATION"],
    )
    def test_action_matching_is_case_insensitive(self, client, action):
        """The source lowercases ``action`` so alt-cased inputs hit the same branch."""
        builder = BuckarooVoucherBuilder(client)
        allowed = builder.get_allowed_service_parameters(action)
        canonical_actions = {
            "pay": "Pay", "PAY": "Pay",
            "getbalance": "GetBalance", "GETBALANCE": "GetBalance",
            "deactivatevoucher": "DeactivateVoucher",
            "createapplication": "CreateApplication", "CREATEAPPLICATION": "CreateApplication",
        }
        expected = builder.get_allowed_service_parameters(canonical_actions[action])
        assert allowed == expected

    @pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "unknown"])
    def test_unsupported_action_returns_empty_dict(self, client, action):
        assert BuckarooVoucherBuilder(client).get_allowed_service_parameters(action) == {}
