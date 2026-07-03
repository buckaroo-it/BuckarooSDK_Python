from typing import Dict, Any
from .payment_builder import PaymentBuilder
from ...models.payment_response import PaymentResponse


class BankingBuilder(PaymentBuilder):
    """Builder for Banking payouts.

    Banking is a payout: Buckaroo sends money OUT to a bank account given an
    IBAN and account holder name. Unlike the base Pay flow, it uses the
    ``PaymentOrder`` action, sends ``AmountCredit`` (not ``AmountDebit``), and
    has no return URLs since it's a server-to-server payout with no redirect.
    """

    def get_service_name(self) -> str:
        """Get the service name for Banking payouts."""
        return "Banking"

    def get_allowed_service_parameters(self, action: str = "PaymentOrder") -> Dict[str, Any]:
        """Get the allowed service parameters for Banking payouts based on action."""

        if action.lower() in ["paymentorder"]:
            return {
                "accountholdername": {
                    "type": str,
                    "required": True,
                    "description": "Account holder name",
                },
                "iban": {"type": str, "required": True, "description": "IBAN"},
            }

        return {}

    def required_fields(self, action: str = "PaymentOrder") -> Dict[str, Any]:
        """Banking is a server-to-server payout with no redirect, so it drops the
        ``return_url*`` requirements. Currency, amount, and invoice stay required."""
        if action.lower() == "paymentorder":
            return {
                "currency": self._currency,
                "amount_debit": self._amount_debit,
                "invoice": self._invoice,
            }
        return super().required_fields(action)

    def payment_order(self, validate: bool = True) -> PaymentResponse:
        """Execute the Banking payout.

        Uses AmountCredit (not AmountDebit) per Buckaroo API requirements.
        """
        payment_request = self.build("PaymentOrder", validate=validate)
        request_data = payment_request.to_dict()

        # PaymentRequest.to_dict always writes AmountDebit; swap to AmountCredit
        # since Buckaroo expects AmountCredit for payouts.
        request_data["AmountCredit"] = request_data.pop("AmountDebit")

        return self._post_transaction(request_data)
