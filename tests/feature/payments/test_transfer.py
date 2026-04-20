from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestTransferFeature:
    def test_transfer_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="transfer", invoice="INV-TRF-001",
            payload_overrides={"description": "Test transfer"},
            service_params={
                "customeremail": "test@example.com",
                "customerfirstname": "John",
                "customerlastname": "Doe",
            },
        )

    def test_transfer_cancel(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "transfer", "Action": "Cancel", "Parameters": []}],
            "ServiceCode": "transfer",
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("transfer", TestHelpers.standard_payload(
            invoice="INV-TRFC-001",
            description="Cancel",
            original_transaction_key="some-key",
            service_parameters={
                "customeremail": "test@example.com",
                "customerfirstname": "John",
                "customerlastname": "Doe",
            },
        )).cancel()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
