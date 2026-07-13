#!/usr/bin/env python3
"""Demo of the Pay Per Email payment method.

Pay Per Email emails the shopper a payment link instead of returning an inline
redirect. The demo drives the ``PaymentInvitation`` action, passing the customer
identity (email, name, gender) as service parameters. Gated on
``BUCKAROO_STORE_KEY`` / ``BUCKAROO_SECRET_KEY`` env vars.
"""

import os
import sys

# Add parent directory to Python path so the demo can import the SDK in-place.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo


def _have_credentials() -> bool:
    if not os.getenv("BUCKAROO_STORE_KEY") or not os.getenv("BUCKAROO_SECRET_KEY"):
        print("⚠️  Set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY to run this demo")
        return False
    return True


def demo_payment_invitation() -> None:
    """Send a Pay Per Email invitation via the PaymentInvitation action."""
    print("\n1. Pay Per Email invitation")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()

        # ExpirationDate is optional; omit it to use the account default. Gender
        # follows Buckaroo's codes: 1=Male, 2=Female, 0=Unknown, 9=N/A.
        response = app.payments.create_payment(
            "payperemail",
            {
                "currency": "EUR",
                "amount": 42.00,
                "description": "pay per email demo",
                "invoice": "PPE-DEMO-001",
                "return_url": "https://www.buckaroo.nl",
                "return_url_cancel": "https://www.buckaroo.nl/cancel",
                "return_url_error": "https://www.buckaroo.nl/error",
                "return_url_reject": "https://www.buckaroo.nl/reject",
                "service_parameters": {
                    "CustomerEmail": "john@example.com",
                    "CustomerFirstName": "John",
                    "CustomerLastName": "Doe",
                    "CustomerGender": "1",
                    "ExpirationDate": "2026-12-31",
                },
            },
        ).execute_action("PaymentInvitation")
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — PAY PER EMAIL DEMO")
    print("=" * 60)
    demo_payment_invitation()
    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
