from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestSepadirectdebitFeature:
    """Feature tests for SEPA Direct Debit payment method with mandate parameters."""

    def test_sepadirectdebit_pay_returns_pending(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("sepadirectdebit")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sepadirectdebit", {
            "amount": 10.00, "currency": "EUR", "description": "Test SEPA DD",
            "invoice": "INV-SEPA-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {
                "customerIBAN": "NL91ABNA0417164300",
                "customerBIC": "ABNANL2A",
                "mandateReference": "MANDATE-001",
                "mandateDate": "2024-01-01",
                "customerAccountName": "John Doe",
            },
        }).pay()
        assert response.is_pending()
