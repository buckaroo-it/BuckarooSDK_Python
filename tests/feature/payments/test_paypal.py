from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPaypalFeature:
    def test_paypal_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="paypal", invoice="INV-PP-001",
            payload_overrides={"description": "Test paypal"},
        )

    def test_paypal_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("paypal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paypal", TestHelpers.standard_payload(
            invoice="INV-PPR-001",
            description="Refund",
            original_transaction_key="some-key",
        )).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
