#!/usr/bin/env python3
"""Demo of the Split Payments (``Marketplaces``) solution.

Marketplaces lets a platform divide one customer payment across its own funds
account and one or more seller accounts, move held funds later, refund from
sellers, and move funds manually between accounts. Following the other Buckaroo
SDKs, ``split`` and ``refund_supplementary`` build a supplementary service that
is *combined* into a payment or refund; ``transfer`` and ``manual_transfer`` are
standalone. Gated on ``BUCKAROO_STORE_KEY`` / ``BUCKAROO_SECRET_KEY`` env vars.

The account IDs, issuer, and transaction keys below are placeholders — replace
them with values from your own Split Payments setup to run against the sandbox.
"""

import os
import sys

# Add parent directory to Python path so the demo can import the SDK in-place.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo

# Placeholder identifiers — replace with your own Split Payments values.
ISSUER = "ABNANL2A"
SELLER_1 = "789C60F316D24B088ACD471"
SELLER_2 = "369C60F316D24B088ACD238"
FUNDS_ACCOUNT = "AAAAAAAAAAAAAAAAAAAAAAA"
SPLIT_TXN_KEY = "REPLACE_WITH_SPLIT_TRANSACTION_KEY"


def _have_credentials() -> bool:
    if not os.getenv("BUCKAROO_STORE_KEY") or not os.getenv("BUCKAROO_SECRET_KEY"):
        print("⚠️  Set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY to run this demo")
        return False
    return True


def demo_split() -> None:
    """Split: build the split, combine it into an iDEAL payment."""
    print("\n1. Split")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        marketplaces = app.solutions.create_solution("marketplaces").split(
            {
                "daysUntilTransfer": "2",
                "marketplace": {
                    "Amount": "10.00",
                    "InvoiceNumber": "INV0000123",
                    "Description": "INV0001 Commission Platform",
                },
                "sellers": [
                    {"AccountId": SELLER_1, "Amount": "50.00", "Description": "Payout 1"},
                    {"AccountId": SELLER_2, "Amount": "35.00", "Description": "Payout 2"},
                ],
            }
        )
        response = (
            app.payments.create_payment(
                "ideal",
                {
                    "currency": "EUR",
                    "amount": 95.00,
                    "invoice": "INV0001",
                    "description": "Split order INV0001",
                    "service_parameters": {"issuer": ISSUER},
                    "return_url": "https://example.com/return",
                    "return_url_cancel": "https://example.com/cancel",
                    "return_url_error": "https://example.com/error",
                    "return_url_reject": "https://example.com/reject",
                },
            )
            .combine(marketplaces)
            .pay()
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_transfer_all() -> None:
    """Transfer (I): release every held split of an existing split payment."""
    print("\n2. Transfer (I) — transfer all")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution("marketplaces").transfer(
            {"originalTransactionKey": SPLIT_TXN_KEY}
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_transfer_partial() -> None:
    """Transfer (II): re-specify the split (partial/different distribution)."""
    print("\n3. Transfer (II) — partial / re-specified")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution("marketplaces").transfer(
            {
                "originalTransactionKey": SPLIT_TXN_KEY,
                "marketplace": {"Amount": "10.00", "Description": "INV0001 Commission Platform"},
                "sellers": [{"AccountId": SELLER_1, "Amount": "50.00"}],
            }
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_refund_supplementary_all() -> None:
    """RefundSupplementary (I): refund the consumer and revert all transfers."""
    print("\n4. RefundSupplementary (I) — revert all")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        marketplaces = app.solutions.create_solution("marketplaces").refund_supplementary()
        response = (
            app.payments.create_payment(
                "ideal",
                {
                    "currency": "EUR",
                    "amount": 50.00,
                    "invoice": "INV0001",
                    "description": "Split refund INV0001",
                    "original_transaction_key": SPLIT_TXN_KEY,
                    "refund_amount": 50.00,
                    "return_url": "https://example.com/return",
                    "return_url_cancel": "https://example.com/cancel",
                    "return_url_error": "https://example.com/error",
                    "return_url_reject": "https://example.com/reject",
                },
            )
            .combine(marketplaces)
            .refund()
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_refund_supplementary_partial() -> None:
    """RefundSupplementary (II): retrieve specific amounts per seller."""
    print("\n5. RefundSupplementary (II) — per-seller")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        marketplaces = app.solutions.create_solution("marketplaces").refund_supplementary(
            {
                "sellers": [
                    {
                        "AccountId": SELLER_1,
                        "Amount": "30.00",
                        "Description": "INV0001 Refund Beauty Products BV",
                    }
                ]
            }
        )
        response = (
            app.payments.create_payment(
                "ideal",
                {
                    "currency": "EUR",
                    "amount": 30.00,
                    "invoice": "INV0001",
                    "description": "Split refund INV0001",
                    "original_transaction_key": SPLIT_TXN_KEY,
                    "refund_amount": 30.00,
                    "return_url": "https://example.com/return",
                    "return_url_cancel": "https://example.com/cancel",
                    "return_url_error": "https://example.com/error",
                    "return_url_reject": "https://example.com/reject",
                },
            )
            .combine(marketplaces)
            .refund()
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_manual_transfer() -> None:
    """ManualTransfer: move funds directly between two accounts."""
    print("\n6. ManualTransfer")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution("marketplaces").manual_transfer(
            {
                "fromAccountId": SELLER_1,
                "toAccountId": FUNDS_ACCOUNT,
                "fromDescription": "Deduction monthly fee",
                "toDescription": "Monthly fee third party ABC",
                "amount": 10.00,
                "currency": "EUR",
                "invoice": "INV0001",
            }
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — SPLIT PAYMENTS (MARKETPLACES) DEMO")
    print("=" * 60)

    demo_split()
    demo_transfer_all()
    demo_transfer_partial()
    demo_refund_supplementary_all()
    demo_refund_supplementary_partial()
    demo_manual_transfer()

    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
