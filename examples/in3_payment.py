#!/usr/bin/env python3
"""
In3 payment example.

In3 is a buy-now-pay-later method that requires billing/shipping customer
details and a list of articles (line items) to be sent with the payment.

Run:
  BUCKAROO_STORE_KEY=... BUCKAROO_SECRET_KEY=... python examples/in3_payment.py
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


# ── 1. Pay ────────────────────────────────────────────────────────────────────

def example_pay():
    """
    In3 requires billing customer, shipping customer, and a list of articles.
    Articles are passed as a list of dicts — the SDK expands them into
    grouped parameters automatically.
    """
    response = app.payments.create_payment("in3", {
        "currency":         "EUR",
        "amount":           49.50,
        "description":      "Order #3001",
        "invoice":          "INV-3001",
        "return_url":       f"{RETURN_BASE}/return",
        "return_url_cancel":f"{RETURN_BASE}/cancel",
        "return_url_error": f"{RETURN_BASE}/error",
        "return_url_reject":f"{RETURN_BASE}/reject",
        "service_parameters": {
            "billingCustomer": {
                "category":      "Person",
                "gender":        "Male",
                "initials":      "J",
                "lastName":      "Doe",
                "birthDate":     "1990-01-01",
                "street":        "Hoofdstraat",
                "houseNumber":   "12",
                "zipcode":       "1234AB",
                "city":          "Amsterdam",
                "country":       "NL",
                "email":         "j.doe@example.com",
                "phone":         "0612345678",
            },
            "shippingCustomer": {
                "street":      "Hoofdstraat",
                "houseNumber": "12",
                "zipcode":     "1234AB",
                "city":        "Amsterdam",
                "country":     "NL",
            },
            "article": [
                {
                    "description":    "Blue T-shirt (L)",
                    "identifier":     "TSHIRT-001",
                    "quantity":       2,
                    "price":          19.99,
                    "vatCategory":    "High",
                },
                {
                    "description":    "Shipping costs",
                    "identifier":     "SHIPPING",
                    "quantity":       1,
                    "price":          9.52,
                    "vatCategory":    "High",
                },
            ],
        },
    }).pay()

    print_response("In3 Pay", response)
    return response


# ── 2. Refund ─────────────────────────────────────────────────────────────────

def example_refund(original_transaction_key: str):
    """Full refund of a completed In3 payment."""
    builder = app.payments.create_payment("in3", {
        "currency":         "EUR",
        "amount":           49.50,
        "description":      "Refund for Order #3001",
        "invoice":          "INV-3001",
        "return_url":       f"{RETURN_BASE}/return",
        "return_url_cancel":f"{RETURN_BASE}/cancel",
        "return_url_error": f"{RETURN_BASE}/error",
        "return_url_reject":f"{RETURN_BASE}/reject",
    })

    response = builder.refund(original_transaction_key=original_transaction_key)
    print_response("In3 Refund", response)
    return response


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("IN3 PAYMENT EXAMPLES")
    print("=" * 55)

    pay_response = example_pay()

    txn_key = pay_response.transaction_key or "REPLACE_WITH_REAL_TXN_KEY"
    example_refund(txn_key)
