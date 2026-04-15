from typing import Dict, Any, Optional

from ..base_builder import BaseBuilder
from ...models.payment_response import PaymentResponse
from ...models.transaction_context import TransactionContext
from ...exceptions._parameter_validation_error import ParameterValidationError, RequiredParameterMissingError


class PaymentBuilder(BaseBuilder):
    """Base class for all payment method builders.

    Adds the payment lifecycle on top of the shared builder scaffolding in
    ``BaseBuilder``: pay, refund, capture, cancel, and their helpers.

    ``SolutionBuilder`` inherits from ``BaseBuilder`` directly and intentionally
    does *not* get these methods.
    """

    # ── Primary action ────────────────────────────────────────────────────────

    def pay(self, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Execute the payment.

        Args:
            validate: Validate and filter service parameters before building.
            strict_validation: Raise on invalid parameters instead of filtering.

        Raises:
            RequiredParameterMissingError: If a required field is missing.
            ParameterValidationError: If a service parameter is invalid (strict mode).
            AuthenticationError: If HMAC authentication fails.
        """
        request_data = self.build("Pay", validate=validate, strict_validation=strict_validation).to_dict()
        return self._post_transaction(request_data)

    # ── Follow-up operations ──────────────────────────────────────────────────

    def refund(self, ctx: Optional[TransactionContext] = None, validate: bool = True) -> PaymentResponse:
        """Execute a full refund.

        Args:
            ctx: Carries ``original_transaction_key`` and an optional ``amount``
                 override.  Falls back to ``_payload['originalTransactionKey']``
                 when omitted (set by ``from_dict()``).

        Raises:
            RequiredParameterMissingError: If no transaction key can be resolved.
        """
        txn_key = (ctx.original_transaction_key if ctx else None) or self._payload.get('originalTransactionKey')
        if not txn_key:
            raise RequiredParameterMissingError("originalTransactionKey", action="Refund")

        refund_amount = (ctx.amount if ctx else None) or self._payload.get('refund_amount')
        request_data = self._build_keyed_request('Refund', txn_key, validate=validate)

        if refund_amount is not None:
            request_data['AmountCredit'] = refund_amount
            request_data.pop('AmountDebit', None)
        else:
            if 'AmountDebit' in request_data:
                request_data['AmountCredit'] = request_data.pop('AmountDebit')

        return self._post_transaction(request_data)

    def partial_refund(self, ctx: TransactionContext) -> PaymentResponse:
        """Execute a partial refund.

        Args:
            ctx: ``ctx.amount`` must be set and greater than 0.

        Raises:
            ParameterValidationError: If ``ctx.amount`` is missing or non-positive.
        """
        if not ctx.amount or ctx.amount <= 0:
            raise ParameterValidationError(
                "Partial refund amount must be greater than 0",
                parameter_name="refund_amount",
                action="Refund",
            )
        return self.refund(ctx)

    def capture(self, ctx: Optional[TransactionContext] = None, validate: bool = True) -> PaymentResponse:
        """Capture a previously authorized payment.

        Args:
            ctx: ``ctx.original_transaction_key`` is the authorization key;
                 ``ctx.amount`` overrides the capture amount when set.
                 Falls back to ``_payload`` when omitted.

        Raises:
            RequiredParameterMissingError: If no transaction key can be resolved.
        """
        auth_key = (
            (ctx.original_transaction_key if ctx else None)
            or self._payload.get('authorization_key')
            or self._payload.get('original_transaction_key')
        )
        if not auth_key:
            raise RequiredParameterMissingError("originalTransactionKey", action="Capture")

        capture_amount = (ctx.amount if ctx else None) or self._payload.get('capture_amount')
        request_data = self._build_keyed_request('Capture', auth_key, validate=validate)

        if capture_amount is not None:
            request_data['AmountDebit'] = capture_amount

        return self._post_transaction(request_data)

    def cancel(self, ctx: Optional[TransactionContext] = None) -> PaymentResponse:
        """Cancel a pending or authorized transaction.

        Args:
            ctx: Carries the transaction key to cancel.
                 Falls back to ``_payload`` when omitted.

        Raises:
            RequiredParameterMissingError: If no transaction key can be resolved.
        """
        txn_key = (
            (ctx.original_transaction_key if ctx else None)
            or self._payload.get('cancel_key')
            or self._payload.get('original_transaction_key')
        )
        if not txn_key:
            raise RequiredParameterMissingError("originalTransactionKey", action="Cancel")

        request_data = self._build_keyed_request('Pay', txn_key)
        request_data.pop('AmountDebit', None)
        request_data.pop('AmountCredit', None)

        return self._post_transaction(request_data)

    # ── Generic action helper ─────────────────────────────────────────────────

    def execute_action(self, action: str, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Execute any named action supported by this payment method.

        Used by capability mixins (``pay_encrypted``, ``instant_refund``, etc.)
        and by concrete builder methods that map directly to a single Buckaroo action.

        Args:
            action: Buckaroo action string, e.g. ``'PayEncrypted'``, ``'instantRefund'``.
            validate: Validate and filter service parameters before building.
            strict_validation: Raise on invalid parameters instead of filtering.
        """
        request_data = self.build(action, validate=validate, strict_validation=strict_validation).to_dict()
        return self._post_transaction(request_data)

    # ── Internal helper ───────────────────────────────────────────────────────

    def _build_keyed_request(self, action: str, txn_key: str, validate: bool = True) -> Dict[str, Any]:
        """Build a request dict that references an original transaction.

        Sets ``OriginalTransactionKey`` so callers only need to handle
        any additional amount/field adjustments.
        """
        request_data = self.build(action, validate=validate).to_dict()
        request_data['OriginalTransactionKey'] = txn_key
        return request_data
