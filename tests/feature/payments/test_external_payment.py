"""Feature test: externalPayment is unreachable due to camelCase registry key."""

import pytest

from buckaroo.builders.payments.default_builder import DefaultBuilder
from buckaroo.builders.payments.external_payment_builder import ExternalPaymentBuilder
from buckaroo.factories.payment_method_factory import PaymentMethodFactory
from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestExternalPaymentFeature:
    def test_factory_lookup_falls_back_to_default(self):
        """The camelCase key 'externalPayment' is unreachable because
        create_builder() lowercases the input to 'externalpayment',
        which has no registry entry. The factory silently returns
        DefaultBuilder instead of ExternalPaymentBuilder."""
        builder = PaymentMethodFactory.create_builder("externalPayment", None)
        assert isinstance(builder, DefaultBuilder)
        assert not isinstance(builder, ExternalPaymentBuilder)

    @pytest.mark.xfail(
        strict=True,
        reason="Registry key 'externalPayment' is camelCase but create_builder() "
               "lowercases input to 'externalpayment', so ExternalPaymentBuilder "
               "is never used; DefaultBuilder handles it instead",
    )
    def test_external_payment_uses_correct_builder(self):
        """Should resolve to ExternalPaymentBuilder, but doesn't."""
        builder = PaymentMethodFactory.create_builder("externalPayment", None)
        assert isinstance(builder, ExternalPaymentBuilder)

    @pytest.mark.xfail(
        strict=True,
        reason="Registry key 'externalPayment' is camelCase but create_builder() "
               "lowercases input, making ExternalPaymentBuilder unreachable",
    )
    def test_external_payment_pay(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("externalPayment")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("externalPayment", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test external payment",
            "invoice": "INV-EXT-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        assert response.currency == "EUR"
        assert response.amount_debit == 10.00
        assert response.service_code == "ExternalPayment"
