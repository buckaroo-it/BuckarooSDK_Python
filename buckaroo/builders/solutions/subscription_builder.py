from typing import Dict, Any
from .solution_builder import SolutionBuilder


class SubscriptionBuilder(SolutionBuilder):
    """Builder for Subscription solutions with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Subscription solutions."""
        return "Subscription"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Subscription based on action."""

        if action.lower() in ["pay"]:
            return {}

        return {}

    def create_subscription(self, validate: bool = True) -> Any:
        """Create a subscription."""
        payload = self.build("CreateSubscription", validate=validate)
        return self._post_data_request(payload.to_dict())