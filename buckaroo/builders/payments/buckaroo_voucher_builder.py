from typing import Dict, Any
from .payment_builder import PaymentBuilder


class BuckarooVoucherBuilder(PaymentBuilder):
    """Builder for Buckaroo Voucher payments."""

    def get_service_name(self) -> str:
        """Get the service name for Buckaroo Voucher payments."""
        return "Buckaroo Voucher"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Buckaroo Voucher payments based on action."""

        if action.lower() in ["pay", "getbalance", "deactivatevoucher"]:
            return {
                "VoucherCode": {
                    "type": str,
                    "required": True,
                    "description": "The voucher code to use for the payment",
                },
            }

        if action.lower() in ["createapplication"]:
            return {
                "GroupReference": {
                    "type": str,
                    "required": False,
                    "description": "The group reference for the application",
                },
                "UsageType": {
                    "type": str,
                    "required": True,
                    "description": "The usage type for the voucher application",
                },
                "ValidFrom": {
                    "type": str,
                    "required": True,
                    "description": "The start date of voucher validity",
                },
                "ValidUntil": {
                    "type": str,
                    "required": False,
                    "description": "The end date of voucher validity",
                },
                "CreationBalance": {
                    "type": float,
                    "required": True,
                    "description": "The initial balance of the voucher",
                },
            }

        return {}
