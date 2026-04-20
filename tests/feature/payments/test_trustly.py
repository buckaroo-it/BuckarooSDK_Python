from tests.support.test_helpers import TestHelpers


class TestTrustlyFeature:
    def test_trustly_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="trustly", invoice="INV-TRS-001",
            payload_overrides={"description": "Test trustly"},
            service_params={
                "customerFirstName": "John",
                "customerLastName": "Doe",
                "customerCountryCode": "NL",
                "consumeremail": "john@example.com",
            },
        )

    def test_trustly_refund(self, buckaroo, mock_strategy):
        TestHelpers.assert_refund_returns_success(
            buckaroo, mock_strategy,
            method="trustly", invoice="INV-TRSR-001",
            original_transaction_key="some-key",
        )
