#!/usr/bin/env python3
"""
iDEAL payment examples.

Covers:
  - Pay (with and without pre-selected bank)
  - Full refund
  - Partial refund
  - Instant refund

Run:
  BUCKAROO_STORE_KEY=... BUCKAROO_SECRET_KEY=... python examples/ideal_payment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo
from buckaroo.models import TransactionContext

RETURN_BASE = "https://yourshop.com"

app = Buckaroo.quick_setup(
    store_key=os.environ["BUCKAROO_STORE_KEY"],
    secret_key=os.environ["BUCKAROO_SECRET_KEY"],
    mode="test",
)


# ── helpers ───────────────────────────────────────────────────────────────────

def print_response(label, response):
    print(f"\n{'─' * 55}")
    print(f"  {label}")
    print(f"{'─' * 55}")
    print(f"  HTTP status   : {response.status_code}")
    print(f"  Success       : {response.success}")
    if response.status:
        print(f"  Buckaroo code : {response.status.code.code} — {response.status.code.description}")
    if response.requires_action():
        print(f"  Redirect URL  : {response.get_redirect_url()}")
    if response.transaction_key:
        print(f"  Txn key       : {response.transaction_key}")


def base_builder():
    """Return a pre-filled iDEAL builder ready to customise."""
    return (
        app.payments.create_payment("ideal")
        .currency("EUR")
        .amount(25.50)
        .description("Order #1042")
        .invoice("INV-1042")
        .return_url(f"{RETURN_BASE}/return")
        .return_url_cancel(f"{RETURN_BASE}/cancel")
        .return_url_error(f"{RETURN_BASE}/error")
        .return_url_reject(f"{RETURN_BASE}/reject")
        .push_url(f"{RETURN_BASE}/push")
    )



# ── 1. Pay (Buckaroo shows bank picker) ───────────────────────────

def example_pay():
    """
    Omit the issuer.  Buckaroo redirects the customer to its own bank-selection
    page.  Simpler integration, slightly more friction for the customer.
    """
    response = base_builder().pay()
    print_response("Pay — Buckaroo bank picker", response)
    return response


# ── 2. Full refund ────────────────────────────────────────────────────────────

def example_full_refund(original_transaction_key: str):
    """
    Refund the full amount of a completed transaction.
    The amount is read from the builder — no need to specify it again.
    """
    ctx = TransactionContext(original_transaction_key=original_transaction_key)
    response = base_builder().refund(ctx)
    print_response("Full refund", response)
    return response


# ── 3. Partial refund ─────────────────────────────────────────────────────────

def example_partial_refund(original_transaction_key: str):
    """Refund only part of the original amount."""
    ctx = TransactionContext(original_transaction_key=original_transaction_key, amount=10.00)
    response = base_builder().partial_refund(ctx)
    print_response("Partial refund (€10.00)", response)
    return response


# ── 4. Instant refund ─────────────────────────────────────────────────────────

def example_instant_refund():
    """
    Instant refund sends money back immediately without a separate push
    notification cycle.  Buckaroo must have the customer IBAN on file.
    """
    response = base_builder().instant_refund()
    print_response("Instant refund", response)
    return response


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("iDEAL PAYMENT EXAMPLES")
    print("=" * 55)

    # Run the pay examples
    pay_response = example_pay()
    example_pay()

    # Use the transaction key from the first payment for follow-up examples.
    # In a real application you would store this key after receiving the push
    # notification confirming the payment was successful.
    txn_key = pay_response.transaction_key or "REPLACE_WITH_REAL_TXN_KEY"

    example_full_refund(txn_key)
    example_partial_refund(txn_key)
    example_instant_refund()
