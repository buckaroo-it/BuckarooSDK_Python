"""Feature test: voucher pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestVoucherFeature:
    def test_voucher_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="voucher",
            invoice="INV-VOU-001",
            payload_overrides={"description": "Test voucher"},
            service_params={
                "article": [
                    {
                        "identifier": "ART-001",
                        "description": "Test Article",
                        "quantity": "1",
                        "price": "10.00",
                    },
                ],
            },
        )
