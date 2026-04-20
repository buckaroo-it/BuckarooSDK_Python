from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestCreditcardFeature:
    """Feature tests for creditcard payment method with all capability actions."""

    def test_creditcard_pay(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "Pay")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-001",
            description="Test pay",
        )).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("creditcard")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-002",
            description="Test refund",
            original_transaction_key="ABC123",
        )).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_authorize(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "Authorize")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-003",
            description="Test authorize",
        )).authorize()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_capture(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "creditcard", "Action": "Capture", "Parameters": []}],
            "ServiceCode": "creditcard",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-004",
            description="Test capture",
            original_transaction_key="ABC123",
        )).capture()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_cancel_authorize(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "creditcard", "Action": "CancelAuthorize", "Parameters": []}],
            "ServiceCode": "creditcard",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-005",
            description="Test cancel authorize",
            original_transaction_key="ABC123",
        )).cancelAuthorize()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_pay_encrypted(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "PayEncrypted")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-006",
            description="Test pay encrypted",
        ))
        builder.add_parameter("EncryptedCardData", "encrypted-data-here")
        response = builder.payEncrypted()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_pay_with_security_code(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "PayWithSecurityCode")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-007",
            description="Test pay with security code",
        ))
        builder.add_parameter("EncryptedSecurityCode", "encrypted-code-here")
        response = builder.payWithSecurityCode()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_pay_with_token(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "PayWithToken")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-008",
            description="Test pay with token",
        ))
        builder.add_parameter("SessionId", "session-token-123")
        response = builder.payWithToken()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_pay_recurrent(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "creditcard", "Action": "PayRecurrent", "Parameters": []}],
            "ServiceCode": "creditcard",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-009",
            description="Test pay recurrent",
            original_transaction_key="ABC123",
        )).payRecurrent()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_creditcard_authorize_encrypted(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "AuthorizeEncrypted")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-010",
            description="Test authorize encrypted",
        ))
        builder.add_parameter("EncryptedCardData", "encrypted-data-here")
        response = builder.authorizeEncrypted()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_creditcard_authorize_with_token(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("creditcard", "AuthorizeWithToken")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        builder = buckaroo.payments.create_payment("creditcard", TestHelpers.standard_payload(
            invoice="INV-CC-011",
            description="Test authorize with token",
        ))
        builder.add_parameter("SessionId", "session-token-456")
        response = builder.authorizeWithToken()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
