from __future__ import annotations

from typing import Any, Dict

try:
    from typing import Self
except ImportError:  # Python < 3.11
    from typing_extensions import Self

from ...models.payment_request import Parameter, PaymentRequest
from .payment_builder import PaymentBuilder


class PosBuilder(PaymentBuilder):
    """Builder for Point of Sale (POS) payments.

    POS transactions are PIN-based in-store payments processed through a
    physical payment terminal. The merchant initiates the transaction via
    API with the terminal's unique ``TerminalID``; Buckaroo routes the
    request to that terminal, which prompts the customer to complete
    payment there.

    The immediate response carries a pending/awaiting status — the final
    result, plus the printable ``Ticket`` receipt data, arrives later via
    push notification once the customer completes payment at the terminal.

    Every POS request is sent with ``Channel: "Web"`` per the Buckaroo POS
    specification; this is fixed internally and not user-configurable.
    Supports the ``Pay`` action only.
    """

    def required_fields(self, action: str = "Pay") -> Dict[str, Any]:
        """POS has no redirect flow — only currency, amount and invoice are required."""
        return {
            "currency": self._currency,
            "amount_debit": self._amount_debit,
            "invoice": self._invoice,
        }

    def get_service_name(self) -> str:
        """Get the service name for POS payments."""
        return "pospayment"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for POS payments based on action."""
        if action.lower() == "pay":
            return {
                "TerminalID": {
                    "type": str,
                    "required": True,
                    "description": "Unique identifier of the physical POS terminal",
                },
            }

        return {}

    def terminal_id(self, terminal_id: str) -> Self:
        """Set the unique Terminal ID of the physical POS terminal.

        Buckaroo routes the transaction to this terminal, which then
        prompts the customer to complete payment.

        Raises:
            ValueError: If ``terminal_id`` is empty or blank.
        """
        if not terminal_id or not str(terminal_id).strip():
            raise ValueError("terminal_id must be a non-empty value")

        self._service_parameters.append(Parameter(name="TerminalID", value=str(terminal_id)))
        return self

    def build(
        self, action: str = "Pay", validate: bool = True, strict_validation: bool = False
    ) -> PaymentRequest:
        """Build the request, forcing ``Channel`` to ``"Web"``.

        Every POS transaction must use the Web channel regardless of any
        value set via the generic :meth:`channel` setter.
        """
        self._channel = "Web"
        return super().build(action, validate=validate, strict_validation=strict_validation)
