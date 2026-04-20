"""Feature test: giftcards pay() round-trip through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestGiftcardsFeature:
    def test_giftcards_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="giftcards", invoice="INV-GC-001",
            payload_overrides={"description": "Test giftcards"},
            service_params={"Cardnumber": "1234567890123456", "PIN": "1234"},
        )
