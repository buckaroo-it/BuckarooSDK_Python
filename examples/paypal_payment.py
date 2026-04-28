#!/usr/bin/env python3
"""
PayPal payment example.

Covers:
  - Pay
  - Refund

Run:
  BUCKAROO_STORE_KEY=... BUCKAROO_SECRET_KEY=... python examples/paypal_payment.py
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
    return (
        app.payments.create_payment("paypal")
        .currency("EUR")
        .amount(35.00)
        .description("Order #4001")
        .invoice("INV-4001")
        .return_url(f"{RETURN_BASE}/return")
        .return_url_cancel(f"{RETURN_BASE}/cancel")
        .return_url_error(f"{RETURN_BASE}/error")
        .return_url_reject(f"{RETURN_BASE}/reject")
        .push_url(f"{RETURN_BASE}/push")
    )


# ── 1. Pay ────────────────────────────────────────────────────────────────────

def example_pay():
    """
    Buckaroo redirects the customer to PayPal to complete the payment.
    The response contains a RedirectURL — send the customer there.
    """
    response = (
        base_builder()
        .add_parameter("buyerEmail", "customer@example.com")
        .add_parameter("productName", "Blue T-shirt")
        .pay()
    )
    print_response("PayPal Pay", response)
    return response


# ── 2. Refund ─────────────────────────────────────────────────────────────────

def example_refund(original_transaction_key: str):
    """Full refund of a completed PayPal payment."""
    response = base_builder().refund(original_transaction_key=original_transaction_key)
    print_response("PayPal Refund", response)
    return response


# ── 3. Partial refund ─────────────────────────────────────────────────────────

def example_partial_refund(original_transaction_key: str):
    """Refund part of a completed PayPal payment."""
    response = base_builder().partial_refund(original_transaction_key=original_transaction_key, amount=10.00)
    print_response("PayPal Partial refund (€10.00)", response)
    return response


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("PAYPAL PAYMENT EXAMPLES")
    print("=" * 55)

    pay_response = example_pay()

    txn_key = pay_response.transaction_key or "REPLACE_WITH_REAL_TXN_KEY"
    example_refund(txn_key)
    example_partial_refund(txn_key)
