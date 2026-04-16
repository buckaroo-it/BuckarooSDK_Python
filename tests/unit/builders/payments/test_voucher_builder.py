"""Per-builder unit tests for :class:`VoucherBuilder`.

Covers construction, the class-level ``_serviceName`` contract, both branches
of ``get_service_name()`` (payload-driven override + ``'Vouchers'`` default),
the ``get_allowed_service_parameters`` snapshot for ``Pay`` (with case
handling), non-Pay actions returning ``{}``, and a ``pay()`` round-trip
through :class:`MockBuckaroo`. Phase 7.36.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.voucher_builder import VoucherBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def client():
    """BuckarooClient wired to a MockBuckaroo strategy — never dispatched."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = MockBuckaroo()
    return c


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    assert isinstance(VoucherBuilder(client), PaymentBuilder)


def test_class_does_not_declare_service_name_attribute():
    """Unlike ``CreditcardBuilder``, ``VoucherBuilder`` does not set
    ``_serviceName`` on the class — the service name is derived dynamically
    from ``_payload['voucher_name']`` with a ``'Vouchers'`` default.
    """
    assert not hasattr(VoucherBuilder, "_serviceName")


def test_get_service_name_defaults_to_vouchers_when_payload_empty(client):
    assert VoucherBuilder(client).get_service_name() == "Vouchers"


def test_get_service_name_reads_voucher_name_from_payload(client):
    builder = VoucherBuilder(client)
    builder._payload["voucher_name"] = "CustomVoucher"
    assert builder.get_service_name() == "CustomVoucher"


ARTICLE_SPEC = {
    "article": {"type": list, "required": True, "description": "Articles"},
}


def test_get_allowed_service_parameters_pay_snapshot(client):
    assert VoucherBuilder(client).get_allowed_service_parameters("Pay") == ARTICLE_SPEC


def test_get_allowed_service_parameters_defaults_to_pay_branch(client):
    """Default ``action='Pay'`` exercises the ``list`` branch without args."""
    assert VoucherBuilder(client).get_allowed_service_parameters() == ARTICLE_SPEC


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    """The source lower-cases ``action`` before comparison."""
    assert (
        VoucherBuilder(client).get_allowed_service_parameters("pay") == ARTICLE_SPEC
    )


@pytest.mark.parametrize(
    "action", ["Refund", "Capture", "Authorize", "Cancel", "UnknownAction"]
)
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert VoucherBuilder(client).get_allowed_service_parameters(action) == {}


def test_pay_posts_transaction_and_parses_response():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "voucher-key-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        VoucherBuilder(client)
        .currency("EUR")
        .amount(25.00)
        .description("Voucher order")
        .invoice("INV-V-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .add_parameter(
            "article",
            [{"Identifier": "A-1", "Description": "Coffee", "Quantity": 1}],
        )
        .pay()
    )

    assert response.key == "voucher-key-1"
    mock.assert_all_consumed()
