from .payment_builder import PaymentBuilder

class ExternalPaymentBuilder(PaymentBuilder):
    """Builder for External payments."""

    def get_service_name(self) -> str:
        """Get the service name for External payments."""
        return "ExternalPayment"
