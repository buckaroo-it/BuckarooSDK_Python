"""
TransactionContext — explicit carrier for follow-up transaction operations.

Pass a ``TransactionContext`` to ``refund()``, ``capture()``, ``cancel()``, and
``cancel_authorize()`` instead of relying on the ``_payload`` side-channel.  This
makes the required inputs visible at the call site and removes hidden state lookups.

Example::

    ctx = TransactionContext(original_transaction_key="ABC123")
    response = builder.refund(ctx)

    ctx = TransactionContext(original_transaction_key="ABC123", amount=5.00)
    response = builder.partial_refund(ctx)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TransactionContext:
    """Carries the identifiers needed for follow-up transaction operations.

    Attributes:
        original_transaction_key: The key of the transaction being referenced
            (authorization, original payment, etc.).
        amount: Optional amount override.  For ``refund``/``partial_refund`` this
            is the credit amount; for ``capture`` this overrides the debit amount.
            When ``None`` the builder uses the amount already on the request.
    """

    original_transaction_key: str
    amount: Optional[float] = None
