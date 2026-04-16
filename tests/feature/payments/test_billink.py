"""Feature tests for Billink payment method."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers

_BILLINK_BASE_PARAMS = {
    "amount": 10.00,
    "currency": "EUR",
    "description": "Test billink",
    "invoice": "INV-BILLINK-001",
    "return_url": "https://example.com/return",
    "return_url_cancel": "https://example.com/cancel",
    "return_url_error": "https://example.com/error",
    "return_url_reject": "https://example.com/reject",
    "service_parameters": {
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
}


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

    def test_billink_pay_with_articles(self, buckaroo, mock_strategy):
        """Articles (cart line items) are included as grouped service parameters."""
        response_body = TestHelpers.pending_redirect_response("billink")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        params = {
            "amount": 25.00,
            "currency": "EUR",
            "description": "Billink with articles",
            "invoice": "INV-BILLINK-ART",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {
                "billingCustomer": [
                    {"firstName": "Jane", "lastName": "Smith", "email": "jane@example.com"},
                ],
                "shippingCustomer": [
                    {"firstName": "Jane", "lastName": "Smith"},
                ],
                "article": [
                    {"description": "Widget", "quantity": "2", "price": "12.50"},
                ],
            },
        }
        response = buckaroo.payments.create_payment("billink", params).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
