"""Feature test: externalPayment resolves to ExternalPaymentBuilder."""

from buckaroo.builders.payments.external_payment_builder import ExternalPaymentBuilder
from buckaroo.factories.payment_method_factory import PaymentMethodFactory
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestExternalPaymentFeature:
    def test_factory_resolves_to_external_payment_builder(self):
        builder = PaymentMethodFactory.create_builder("externalPayment", None)
        assert isinstance(builder, ExternalPaymentBuilder)

    def test_external_payment_pay(self, buckaroo, mock_strategy):
        response_body = Helpers.pending_redirect_response("ExternalPayment")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment(
            "externalPayment",
            Helpers.standard_payload(
                invoice="INV-EXT-001",
                description="Test external payment",
            ),
        )
        assert isinstance(builder, ExternalPaymentBuilder)
        response = builder.pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
