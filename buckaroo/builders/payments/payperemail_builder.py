from typing import Dict, Any
from .payment_builder import PaymentBuilder


class PayPerEmailBuilder(PaymentBuilder):
    """Builder for Pay Per Email payments.

    Pay Per Email drives the ``PaymentInvitation`` action: Buckaroo emails the
    shopper a payment link rather than returning an inline redirect. Customer
    identity (email, name, gender) is supplied as service parameters.
    """

    _serviceName = "payperemail"

    def get_service_name(self) -> str:
        """Get the service name for Pay Per Email payments."""
        return "payperemail"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Pay Per Email based on action.

        Only ``PaymentInvitation`` carries parameters; every other action
        (Pay, Refund, ...) has none.
        """
        if action.lower() == "paymentinvitation":
            return {
                "CustomerGender": {
                    "type": (str, int),
                    "required": True,
                    "description": "Customer gender (1=Male, 2=Female, 0=Unknown, 9=N/A)",
                },
                "CustomerEmail": {
                    "type": str,
                    "required": True,
                    "description": "Customer email address",
                },
                "CustomerFirstName": {
                    "type": str,
                    "required": True,
                    "description": "Customer first name",
                },
                "CustomerLastName": {
                    "type": str,
                    "required": True,
                    "description": "Customer last name",
                },
                "ExpirationDate": {
                    "type": str,
                    "required": False,
                    "description": "Invitation expiration date",
                },
                "PaymentMethodsAllowed": {
                    "type": str,
                    "required": False,
                    "description": "Allowed payment methods (CSV)",
                },
                "MerchantSendsEmail": {
                    "type": (str, bool),
                    "required": False,
                    "description": "Whether the merchant sends the email instead of Buckaroo",
                },
            }

        return {}
