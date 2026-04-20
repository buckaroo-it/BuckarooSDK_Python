"""Feature tests for Billink payment method."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers

_BILLINK_BASE_PARAMS = TestHelpers.standard_payload(
    invoice="INV-BILLINK-001",
    description="Test billink",
    service_parameters={
        "billingCustomer": [
            {"firstName": "John", "lastName": "Doe", "email": "john@example.com"},
        ],
        "shippingCustomer": [
            {"firstName": "John", "lastName": "Doe"},
        ],
        "article": [
            {"description": "Widget", "quantity": "1", "price": "10.00"},
        ],
    },
)


class TestBillinkFeature:
    def test_billink_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("billink")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment(
            "billink", _BILLINK_BASE_PARAMS
        ).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

