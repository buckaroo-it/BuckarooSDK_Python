"""Feature test: externalPayment resolves to ExternalPaymentBuilder."""

from buckaroo.builders.payments.external_payment_builder import ExternalPaymentBuilder
from buckaroo.factories.payment_method_factory import PaymentMethodFactory
from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestExternalPaymentFeature:
    def test_factory_resolves_to_external_payment_builder(self):
        builder = PaymentMethodFactory.create_builder("externalPayment", None)
        assert isinstance(builder, ExternalPaymentBuilder)

    def test_external_payment_pay(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("ExternalPayment")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        builder = buckaroo.payments.create_payment("externalPayment", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test external payment",
            "invoice": "INV-EXT-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        })
        assert isinstance(builder, ExternalPaymentBuilder)
        response = builder.pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
