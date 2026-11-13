#!/usr/bin/env python3
"""
Pay by Bank payment examples.

Covers:
  - Pay (with pre-selected bank)
  - Full refund
  - Partial refund

Run:
  BUCKAROO_STORE_KEY=... BUCKAROO_SECRET_KEY=... python examples/pay_by_bank.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo

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
    """Return a pre-filled Pay by Bank builder ready to customise."""
    return (
        app.payments.create_payment("paybybank")
        .currency("EUR")
        .amount(25.50)
        .description("Order #1043")
        .invoice("INV-1043")
        .return_url(f"{RETURN_BASE}/return")
        .return_url_cancel(f"{RETURN_BASE}/cancel")
        .return_url_error(f"{RETURN_BASE}/error")
        .return_url_reject(f"{RETURN_BASE}/reject")
        .push_url(f"{RETURN_BASE}/push")
    )


# ── 1. Pay (customer's bank pre-selected) ─────────────────────────────────────

def example_pay():
    """
    Pass the customer's bank as the issuer (its BIC code, e.g. ABNANL2A).
    The issuer is required for Pay by Bank.  Send the customer to the
    returned redirect URL to confirm the payment at their bank.
    """
    response = base_builder().add_parameter("issuer", "ABNANL2A").pay()
    print_response("Pay — ABN AMRO pre-selected", response)
    return response


# ── 2. Full refund ────────────────────────────────────────────────────────────

def example_full_refund(original_transaction_key: str):
    """
    Refund the full amount of a completed transaction.
    The amount is read from the builder — no need to specify it again.
    """
    response = base_builder().refund(original_transaction_key=original_transaction_key)
    print_response("Full refund", response)
    return response


# ── 3. Partial refund ─────────────────────────────────────────────────────────

def example_partial_refund(original_transaction_key: str):
    """Refund only part of the original amount."""
    response = base_builder().partial_refund(original_transaction_key=original_transaction_key, amount=10.00)
    print_response("Partial refund (€10.00)", response)
    return response


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("PAY BY BANK PAYMENT EXAMPLES")
    print("=" * 55)

    pay_response = example_pay()

    # Use the transaction key from the payment for the refund examples.
    # In a real application you would store this key after receiving the push
    # notification confirming the payment was successful.
    txn_key = pay_response.transaction_key or "REPLACE_WITH_REAL_TXN_KEY"

    example_full_refund(txn_key)
    example_partial_refund(txn_key)
