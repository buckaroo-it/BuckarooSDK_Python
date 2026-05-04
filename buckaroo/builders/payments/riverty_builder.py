from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.authorize_capture_capable import AuthorizeCaptureCapable


class RivertyBuilder(PaymentBuilder, AuthorizeCaptureCapable):
    """Builder for Riverty (Afterpay New) buy-now-pay-later payments.

    Riverty is the rebrand of AfterPay; the wire service name remains
    ``afterpay``. The method supports Pay, Authorize/Capture/CancelAuthorize,
    and Refund.
    """

    def get_service_name(self) -> str:
        """Get the service name for Riverty payments."""
        return "afterpay"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Riverty payments based on action.

        Pay and Authorize share the same cart-line / customer trio.
        Capture and CancelAuthorize reference the original via top-level
        ``OriginalTransactionKey`` (handled by the SDK), no service params.
        """
        if action.lower() in ("pay", "authorize"):
            return {
                "billingCustomer": {
                    "type": list,
                    "required": True,
                    "description": "Billing customer information",
                },
                "shippingCustomer": {
                    "type": list,
                    "required": True,
                    "description": "Shipping customer information",
                },
                "article": {"type": list, "required": True, "description": "Riverty articles"},
            }

        return {}
