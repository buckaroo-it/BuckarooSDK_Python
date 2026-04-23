from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestDefaultSolutionFeature:
    """Default solution uses the fallback DefaultBuilder since 'default' is not
    registered in SolutionMethodFactory._solution_methods."""

    def test_default_solution_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = Helpers.pending_redirect_response("default")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.solutions.create_solution(
            "default",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-001",
                description="Test default solution",
            ),
        ).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_default_solution_pay_success(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": "default", "Action": "Pay", "Parameters": []}],
                "ServiceCode": "default",
                "AmountDebit": 25.00,
                "Currency": "EUR",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.solutions.create_solution(
            "default",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-002",
                amount=25.00,
                description="Test default solution success",
            ),
        ).pay()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_default_solution_refund(self, buckaroo, mock_strategy):
        response_body = Helpers.refund_response("default")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.solutions.create_solution(
            "default",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-003",
                description="Test default solution refund",
                original_transaction_key="ABCD1234",
            ),
        ).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_default_solution_not_in_factory_registry(self):
        """DefaultBuilder is a fallback, not a registered solution method."""
        from buckaroo.factories.solution_method_factory import SolutionMethodFactory

        assert not SolutionMethodFactory.is_method_supported("default")

    def test_default_solution_service_name_from_payload(self, buckaroo, mock_strategy):
        """DefaultBuilder reads service name from payload's 'method' key."""
        response_body = Helpers.pending_redirect_response("custommethod")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.solutions.create_solution(
            "nonexistent",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-004",
                amount=5.00,
                description="Test custom method fallback",
                method="custommethod",
            ),
        ).pay()
        assert response.is_pending()
