from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestCreditcardFeature:
    """Feature tests for creditcard payment method with all capability actions."""

    def test_creditcard_pay(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "Pay")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test pay",
            "invoice": "INV-CC-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("creditcard")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test refund",
            "invoice": "INV-CC-002",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_authorize(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "Authorize")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test authorize",
            "invoice": "INV-CC-003",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).authorize()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_capture(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "creditcard", "Action": "Capture", "Parameters": []}],
            "ServiceCode": "creditcard",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test capture",
            "invoice": "INV-CC-004",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).capture()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_cancel_authorize(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "creditcard", "Action": "CancelAuthorize", "Parameters": []}],
            "ServiceCode": "creditcard",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test cancel authorize",
            "invoice": "INV-CC-005",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).cancelAuthorize()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_pay_encrypted(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "PayEncrypted")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test pay encrypted",
            "invoice": "INV-CC-006",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        })
        builder.add_parameter("EncryptedCardData", "encrypted-data-here")
        response = builder.payEncrypted()
        assert response.is_pending()
        assert response.get_redirect_url() is not None

    def test_creditcard_pay_with_security_code(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "PayWithSecurityCode")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test pay with security code",
            "invoice": "INV-CC-007",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        })
        builder.add_parameter("EncryptedSecurityCode", "encrypted-code-here")
        response = builder.payWithSecurityCode()
        assert response.is_pending()
        assert response.get_redirect_url() is not None

    def test_creditcard_pay_with_token(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "PayWithToken")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test pay with token",
            "invoice": "INV-CC-008",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        })
        builder.add_parameter("SessionId", "session-token-123")
        response = builder.payWithToken()
        assert response.is_pending()
        assert response.get_redirect_url() is not None

    def test_creditcard_pay_recurrent(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "creditcard", "Action": "PayRecurrent", "Parameters": []}],
            "ServiceCode": "creditcard",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test pay recurrent",
            "invoice": "INV-CC-009",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).payRecurrent()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_authorize_encrypted(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "AuthorizeEncrypted")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test authorize encrypted",
            "invoice": "INV-CC-010",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        })
        builder.add_parameter("EncryptedCardData", "encrypted-data-here")
        response = builder.authorizeEncrypted()
        assert response.is_pending()
        assert response.get_redirect_url() is not None

    def test_creditcard_authorize_with_token(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "AuthorizeWithToken")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", {
            "amount": 10.00, "currency": "EUR", "description": "Test authorize with token",
            "invoice": "INV-CC-011",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        })
        builder.add_parameter("SessionId", "session-token-456")
        response = builder.authorizeWithToken()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
