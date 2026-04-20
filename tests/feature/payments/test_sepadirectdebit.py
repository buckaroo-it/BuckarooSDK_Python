from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestSepadirectdebitFeature:
    """Feature tests for SEPA Direct Debit payment method with mandate parameters."""

    def test_sepadirectdebit_pay_returns_pending(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("sepadirectdebit")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sepadirectdebit", TestHelpers.standard_payload(
            invoice="INV-SEPA-001",
            description="Test SEPA DD",
            service_parameters={
                "customerIBAN": "NL91ABNA0417164300",
                "customerBIC": "ABNANL2A",
                "mandateReference": "MANDATE-001",
                "mandateDate": "2024-01-01",
                "customerAccountName": "John Doe",
            },
        )).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
