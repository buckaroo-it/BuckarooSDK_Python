"""Feature test: bancontact pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestBancontactFeature:
    def test_bancontact_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("bancontact")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("bancontact", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test bancontact payment",
            "invoice": "INV-BANCONTACT-001",
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

    def test_bancontact_pay_encrypted(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response(
            "bancontactmrcash", "PayEncrypted"
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        builder = buckaroo.payments.create_payment("bancontact", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test bancontact encrypted",
            "invoice": "INV-BANCONTACT-ENC",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {
                "encryptedCardData": "encrypted_test_data_abc123",
            },
        })
        response = builder.execute_action("PayEncrypted")

        assert response.is_pending()
        assert response.get_redirect_url() is not None
