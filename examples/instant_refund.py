#!/usr/bin/env python3
"""Demo of instant refunds for iDEAL and Payconiq.

Instant refunds send money back to the shopper immediately instead of via the
regular batch refund process. They are supported for iDEAL and Payconiq
through ``instantRefund()``, which reads ``original_transaction_key`` from the
payload (or an optional argument) and an optional ``refund_amount`` for a
partial refund (a full refund is issued when it's omitted). The refund is
processed as an instant payment on the wire: ``OriginalTransactionKey`` plus
``AmountCredit`` instead of ``AmountDebit``. Gated on ``BUCKAROO_STORE_KEY`` /
``BUCKAROO_SECRET_KEY`` env vars.
"""

import os
import sys

# Add parent directory to Python path so the demo can import the SDK in-place.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo

# Placeholder transaction keys. Replace with the key of a SETTLED iDEAL /
# Payconiq payment before running for real; a live green instant refund also
# requires a merchant account with instant refunds enabled.
_IDEAL_ORIGINAL_TRANSACTION_KEY = "REPLACE_WITH_SETTLED_IDEAL_TRANSACTION_KEY"
_PAYCONIQ_ORIGINAL_TRANSACTION_KEY = "REPLACE_WITH_SETTLED_PAYCONIQ_TRANSACTION_KEY"


def _have_credentials() -> bool:
    if not os.getenv("BUCKAROO_STORE_KEY") or not os.getenv("BUCKAROO_SECRET_KEY"):
        print("⚠️  Set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY to run this demo")
        return False
    return True


def demo_ideal_instant_refund() -> None:
    """Instantly refund part of a settled iDEAL payment."""
    print("\n1. iDEAL instant refund")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()
        response = app.payments.create_payment(
            "ideal",
            {
                "currency": "EUR",
                "description": "ideal instant refund demo",
                "invoice": "IDEAL-REFUND-DEMO-001",
                "original_transaction_key": _IDEAL_ORIGINAL_TRANSACTION_KEY,
                "refund_amount": 12.34,  # optional; omit for full refund
            },
        ).instantRefund()
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_payconiq_instant_refund() -> None:
    """Instantly refund part of a settled Payconiq payment."""
    print("\n2. Payconiq instant refund")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()
        response = app.payments.create_payment(
            "payconiq",
            {
                "currency": "EUR",
                "description": "payconiq instant refund demo",
                "invoice": "PAYCONIQ-REFUND-DEMO-001",
                "original_transaction_key": _PAYCONIQ_ORIGINAL_TRANSACTION_KEY,
                "refund_amount": 12.34,  # optional; omit for full refund
            },
        ).instantRefund()
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — INSTANT REFUND DEMO")
    print("=" * 60)
    demo_ideal_instant_refund()
    demo_payconiq_instant_refund()
    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
