"""Feature test: paybybank pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPaybybankFeature:
    """Feature tests for PayByBank with InstantRefund and FastCheckout capabilities."""

    def test_paybybank_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="paybybank", invoice="INV-PBB-001",
            payload_overrides={"description": "Test paybybank"},
            service_params={"issuer": "INGBNL2A"},
        )

    def test_paybybank_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("paybybank")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", TestHelpers.standard_payload(
            invoice="INV-PBB-REFUND",
            description="Refund",
            original_transaction_key="ABC123",
        )).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_paybybank_instant_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "paybybank", "Action": "InstantRefund", "Parameters": []}],
            "ServiceCode": "paybybank",
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", TestHelpers.standard_payload(
            invoice="INV-PBB-IREFUND",
            description="Instant refund",
            original_transaction_key="ABC123",
        )).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_paybybank_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("paybybank", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", TestHelpers.standard_payload(
            invoice="INV-PBB-FAST",
            description="Fast checkout",
        )).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
