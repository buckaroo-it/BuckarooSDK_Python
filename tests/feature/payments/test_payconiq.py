"""Feature test: payconiq pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPayconiqFeature:
    """Feature tests for Payconiq with InstantRefund and FastCheckout capabilities."""

    def test_payconiq_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="payconiq", invoice="INV-PCQ-001",
            payload_overrides={"description": "Test payconiq"},
        )

    def test_payconiq_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("payconiq")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", TestHelpers.standard_payload(
            invoice="INV-PCQ-REFUND",
            description="Refund",
            original_transaction_key="ABC123",
        )).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_payconiq_instant_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "payconiq", "Action": "InstantRefund", "Parameters": []}],
            "ServiceCode": "payconiq",
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", TestHelpers.standard_payload(
            invoice="INV-PCQ-IREFUND",
            description="Instant refund",
            original_transaction_key="ABC123",
        )).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_payconiq_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("payconiq", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", TestHelpers.standard_payload(
            invoice="INV-PCQ-FAST",
            description="Fast checkout",
        )).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
