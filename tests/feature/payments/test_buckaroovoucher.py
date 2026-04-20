from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestBuckaroovoucherFeature:
    def test_buckaroovoucher_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("buckaroovoucher")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("buckaroovoucher", TestHelpers.standard_payload(
            invoice="INV-BV-001",
            description="Test buckaroovoucher",
            service_parameters={"VoucherCode": "TESTVOUCHER123"},
        )).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
