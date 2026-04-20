from tests.support.test_helpers import TestHelpers


class TestBuckaroovoucherFeature:
    def test_buckaroovoucher_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="buckaroovoucher", invoice="INV-BV-001",
            payload_overrides={"description": "Test buckaroovoucher"},
            service_params={"VoucherCode": "TESTVOUCHER123"},
        )
