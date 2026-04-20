"""Per-builder unit tests for :class:`KlarnaBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
supported action including the grouped article / line-item structure, the
mixin-free baseline (KlarnaBuilder composes no capability mixins despite the
docstring mention of "bank transfer capabilities"), and an end-to-end
``pay()`` dispatch through ``MockBuckaroo``. Phase 7.20.
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
    AuthorizeCaptureCapable,
)
from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
    BankTransferCapabilities,
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
from buckaroo.builders.payments.klarna_builder import KlarnaBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = KlarnaBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_klarna(client):
    assert KlarnaBuilder(client).get_service_name() == "klarna"


def test_get_allowed_service_parameters_pay_snapshot(client):
    """Cart / grouped-article parameter spec. ``billingCustomer`` and
    ``shippingCustomer`` declare the customer groups; ``article`` declares the
    line-item group. All three are marked required lists so the
    ``add_parameter`` list-of-dicts path groups them into Buckaroo's
    ``GroupType`` / ``GroupId`` convention at serialise time."""
    assert KlarnaBuilder(client).get_allowed_service_parameters("Pay") == {
        "billingCustomer": {
            "type": list,
            "required": True,
            "description": "Billing customer information",
        },
        "shippingCustomer": {
            "type": list,
            "required": True,
            "description": "Shipping customer information",
        },
        "article": {
            "type": list,
            "required": True,
            "description": "Klarna articles",
        },
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = KlarnaBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert KlarnaBuilder(client).get_allowed_service_parameters("Refund") == {}


def test_does_not_mix_in_capability_methods(client):
    """KlarnaBuilder subclasses :class:`PaymentBuilder` only — it does not mix
    in any capability. Guard against accidental mixin drift by asserting the
    class hierarchy is capability-free. Baseline builder methods (``pay``,
    ``refund``, ``capture``, ``cancel``) still come from ``BaseBuilder``."""
    builder = KlarnaBuilder(client)
    for capability in (
        AuthorizeCaptureCapable,
        BankTransferCapabilities,
        EncryptedPayCapable,
        FastCheckoutCapable,
        InstantRefundCapable,
    ):
        assert not isinstance(builder, capability)

    for method in ("pay", "refund", "capture", "cancel"):
        assert hasattr(builder, method)
        assert callable(getattr(builder, method))


def test_pay_dispatches_klarna_service_through_mock_buckaroo():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "KL-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(KlarnaBuilder(client), amount=49.95)

    response = builder.pay(validate=False)

    assert response.key == "KL-1"
    mock.assert_all_consumed()
