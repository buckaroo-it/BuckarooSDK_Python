from tests.support.helpers import Helpers


class TestDefaultSolutionFeature:
    """DefaultBuilder is a fallback for unregistered solution methods.

    It inherits from SolutionBuilder (not PaymentBuilder), so it does NOT
    have payment lifecycle methods like pay() or refund().  Callers must
    use the explicit action builders (e.g. create_subscription) or call
    build() directly.
    """

    def test_default_solution_not_in_factory_registry(self):
        """DefaultBuilder is a fallback, not a registered solution method."""
        from buckaroo.factories.solution_method_factory import SolutionMethodFactory

        assert not SolutionMethodFactory.is_method_supported("default")

    def test_default_solution_has_no_pay_method(self, buckaroo):
        """Solution builders do not expose pay() — that belongs to PaymentBuilder."""
        builder = buckaroo.solutions.create_solution(
            "default",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-001",
                description="Test default solution",
            ),
        )
        assert not hasattr(builder, "pay")

    def test_default_solution_has_no_refund_method(self, buckaroo):
        """Solution builders do not expose refund() — that belongs to PaymentBuilder."""
        builder = buckaroo.solutions.create_solution(
            "default",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-002",
                description="Test default solution",
                original_transaction_key="ABCD1234",
            ),
        )
        assert not hasattr(builder, "refund")

    def test_default_solution_can_build_request(self, buckaroo):
        """DefaultBuilder can still construct a PaymentRequest via build()."""
        builder = buckaroo.solutions.create_solution(
            "default",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-003",
                description="Test default solution build",
            ),
        )
        request = builder.build(validate=False).to_dict()
        assert request["Invoice"] == "INV-SOL-DEF-003"

    def test_default_solution_service_name_from_payload(self, buckaroo):
        """DefaultBuilder reads service name from payload's 'method' key."""
        builder = buckaroo.solutions.create_solution(
            "nonexistent",
            Helpers.standard_payload(
                invoice="INV-SOL-DEF-004",
                amount=5.00,
                description="Test custom method fallback",
                method="custommethod",
            ),
        )
        assert builder.get_service_name() == "custommethod"

    def test_default_solution_service_name_fallback_when_no_method_key(self, buckaroo):
        """DefaultBuilder falls back to 'Unknown' when no method key in payload."""
        builder = buckaroo.solutions.create_solution("default")
        assert builder.get_service_name() == "Unknown"
