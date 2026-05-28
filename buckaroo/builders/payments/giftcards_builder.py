from typing import Dict, Any
from .payment_builder import PaymentBuilder
from ...models.payment_response import PaymentResponse


# VVV, webshop, boekenbon, yourgift all run on the Intersolve backend
# and the gateway requires IntersolveCardnumber/IntersolvePIN for them.
INTERSOLVE_BRANDS = frozenset({
    "intersolve",
    "vvvgiftcard",
    "webshopgiftcard",
    "boekenbon",
    "yourgift",
})


class GiftcardsBuilder(PaymentBuilder):
    """Builder for Giftcards payments."""

    def get_service_name(self) -> str:
        """Get the service name for Giftcards payments.

        Buckaroo rejects capitalized "Giftcards" with 491 "is not a valid
        service name"; the umbrella selectable-services flow needs the
        lowercase plural ``giftcards``.
        """
        return self._payload.get("giftcard_name") or "giftcards"

    def pay_redirect(self) -> PaymentResponse:
        """Redirect-mode giftcard pay: no Service entry is sent.

        Buckaroo's hosted page handles brand selection via
        ServicesSelectableByClient.  Sending any service name in the
        ServiceList causes a 491 "No valid subscription found" error because
        the merchant account is subscribed to individual brand codes, not a
        generic "giftcard" service.
        """
        request_data = self.build(action="Pay", validate=False).to_dict()
        request_data.pop("Services", None)
        return self._post_transaction(request_data)

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Giftcards payments based on action."""
        action_lower = action.lower()
        giftcard_name = (self._payload.get("giftcard_name") or "").lower()

        if action_lower == "pay":
            if not giftcard_name:
                # Redirect mode: no brand picked locally, Buckaroo's hosted page
                # collects card details so we must not require any params here.
                return {}
            if giftcard_name in INTERSOLVE_BRANDS:
                return {
                    "IntersolveCardnumber": {"type": str, "required": True, "description": ""},
                    "IntersolvePIN": {"type": str, "required": True, "description": ""},
                }
            if giftcard_name == "fashioncheque":
                return {
                    "FashionChequeCardNumber": {
                        "type": str,
                        "required": True,
                        "description": "Save payment token for future use",
                    },
                    "FashionChequePIN": {
                        "type": str,
                        "required": True,
                        "description": "Save payment token for future use",
                    },
                }
            if giftcard_name == "tcs":
                return {
                    "TCSCardnumber": {"type": str, "required": True, "description": ""},
                    "TCSValidationCode": {"type": str, "required": True, "description": ""},
                }
            return {
                "Cardnumber": {"type": str, "required": True, "description": ""},
                "PIN": {"type": str, "required": True, "description": ""},
                "LastName": {"type": str, "required": False, "description": ""},
                "Email": {"type": str, "required": False, "description": ""},
            }

        if action_lower == "refund":
            # Intersolve giftcard refunds carry LastName + Email (docs.buckaroo.io/
            # docs/giftcards-integration#partial-refunds); Plaza returns status 690
            # without them. Email is allowed-but-optional: callers can't always
            # supply one, so a missing Email defers to Plaza's 690 rather than
            # failing local validation. Non-Intersolve brands need no extra params.
            if giftcard_name in INTERSOLVE_BRANDS:
                return {
                    "LastName": {"type": str, "required": True, "description": ""},
                    "Email": {"type": str, "required": False, "description": ""},
                }
            return {}

        return {}
