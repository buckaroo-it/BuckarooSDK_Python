from tests.support.test_helpers import TestHelpers


class TestClicktopayFeature:
    def test_clicktopay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="clicktopay", invoice="INV-CTP-001",
            payload_overrides={"description": "Test clicktopay"},
        )
