from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestTrustlyFeature:
    def test_trustly_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("trustly")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = buckaroo.payments.create_payment("trustly", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test trustly",
            "invoice": "INV-TRS-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {
                "customerFirstName": "John",
                "customerLastName": "Doe",
                "customerCountryCode": "NL",
                "consumeremail": "john@example.com",
            },
        }).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
