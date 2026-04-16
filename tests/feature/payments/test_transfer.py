from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestTransferFeature:
    def test_transfer_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("transfer")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("transfer", {
            "amount": 10.00, "currency": "EUR", "description": "Test transfer",
            "invoice": "INV-TRF-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {
                "customeremail": "test@example.com",
                "customerfirstname": "John",
                "customerlastname": "Doe",
            },
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_transfer_cancel(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "transfer", "Action": "Cancel", "Parameters": []}],
            "ServiceCode": "transfer",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("transfer", {
            "amount": 10.00, "currency": "EUR", "description": "Cancel",
            "invoice": "INV-TRFC-001",
            "original_transaction_key": "some-key",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {
                "customeremail": "test@example.com",
                "customerfirstname": "John",
                "customerlastname": "Doe",
            },
        }).cancel()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
