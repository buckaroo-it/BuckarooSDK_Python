from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestSubscriptionFeature:
    """Feature tests for the Subscription solution."""

    def test_create_subscription(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {"Name": "Subscription", "Action": "CreateSubscription", "Parameters": []}
                ],
                "ServiceCode": "Subscription",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))
        response = buckaroo.solutions.create_solution(
            "subscription",
            Helpers.standard_payload(
                invoice="INV-SUB-001",
                description="Test subscription",
            ),
        ).createSubscription()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_create_subscription_with_fluent_interface(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {"Name": "Subscription", "Action": "CreateSubscription", "Parameters": []}
                ],
                "ServiceCode": "Subscription",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))
        response = (
            buckaroo.solutions.create_solution("subscription")
            .amount(15.00)
            .currency("EUR")
            .description("Fluent subscription")
            .invoice("INV-SUB-002")
            .return_url("https://example.com/return")
            .return_url_cancel("https://example.com/cancel")
            .return_url_error("https://example.com/error")
            .return_url_reject("https://example.com/reject")
            .createSubscription()
        )
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_subscription_case_insensitive_lookup(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {"Name": "Subscription", "Action": "CreateSubscription", "Parameters": []}
                ],
                "ServiceCode": "Subscription",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))
        response = buckaroo.solutions.create_solution(
            "SUBSCRIPTION",
            Helpers.standard_payload(
                invoice="INV-SUB-CASE",
                description="Case test",
            ),
        ).createSubscription()
        assert response.status.code.code == 190

    def test_subscription_is_available(self, buckaroo):
        assert buckaroo.solutions.is_method_supported("subscription")
