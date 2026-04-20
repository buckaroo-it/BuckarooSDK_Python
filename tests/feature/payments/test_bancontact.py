"""Feature test: bancontact pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestBancontactFeature:
    def test_bancontact_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response = TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="bancontact", invoice="INV-BANCONTACT-001",
            payload_overrides={"description": "Test bancontact payment"},
        )
        assert response.currency == "EUR"
        assert response.amount_debit == 10.00

    def test_bancontact_pay_encrypted(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response(
            "bancontactmrcash", "PayEncrypted"
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        builder = buckaroo.payments.create_payment("bancontact", TestHelpers.standard_payload(
            invoice="INV-BANCONTACT-ENC",
            description="Test bancontact encrypted",
            service_parameters={
                "encryptedCardData": "encrypted_test_data_abc123",
            },
        ))
        response = builder.execute_action("PayEncrypted")

        assert response.is_pending()
        assert response.get_redirect_url() is not None
