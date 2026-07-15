#!/usr/bin/env python3
"""Demo of the In3 payment method.

Shows the regular ``.pay()`` flow and the ABN-AMRO "Zakelijk op rekening"
(business-on-account) ``.authorize()`` / ``.capture()`` flow. All demos are gated
on ``BUCKAROO_STORE_KEY`` / ``BUCKAROO_SECRET_KEY`` env vars.
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


def demo_pay() -> None:
    """Regular In3 flow: pay in three installments."""
    print("\n1. In3 pay")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()

        # CompanyName and CocNumber are optional billingCustomer fields for B2B
        # orders. They ride along in the billingCustomer group; omit them for
        # regular consumer payments.
        billing = _customer()
        billing.update({"CompanyName": "Acme B.V.", "CocNumber": "12345678"})

        response = app.payments.create_payment(
            "in3",
            {
                "currency": "EUR",
                "amount": 250.00,
                "description": "in3 pay demo",
                "invoice": "IN3-PAY-001",
                "return_url": "https://www.buckaroo.nl",
                "return_url_cancel": "https://www.buckaroo.nl/cancel",
                "return_url_error": "https://www.buckaroo.nl/error",
                "return_url_reject": "https://www.buckaroo.nl/reject",
                "service_parameters": {
                    "article": [
                        {"Description": "Widget", "Quantity": "2", "GrossUnitPrice": "125.00"},
                    ],
                    "billingCustomer": [billing],
                    "shippingCustomer": [_customer()],
                },
            },
        ).pay()
        print(f"   status.code={response.status.code.code}  redirect={response.get_redirect_url()}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_authorize_capture() -> None:
    """ABN-AMRO "Zakelijk op rekening": authorize first, capture later.

    This business-on-account flow uses ``.authorize()`` instead of ``.pay()`` and
    requires the ``route`` service parameter set to ``"AbnB2b"``. Note the exact
    Buckaroo field names: ``GrossUnitPrice`` (not Price), ``StreetNumber`` (not
    house number), ``CountryCode`` (not country). Capture needs no service params.
    """
    print("\n2. In3 authorize / capture (ABN-AMRO Zakelijk op rekening)")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()

        billing = _customer()
        billing.update({"Category": "B2B", "CompanyName": "Acme B.V.", "CocNumber": "12345678"})

        authorize_response = app.payments.create_payment(
            "in3",
            {
                "currency": "EUR",
                "amount": 250.00,
                "description": "in3 authorize demo",
                "invoice": "IN3-AUTH-001",
                "return_url": "https://www.buckaroo.nl",
                "return_url_cancel": "https://www.buckaroo.nl/cancel",
                "return_url_error": "https://www.buckaroo.nl/error",
                "return_url_reject": "https://www.buckaroo.nl/reject",
                "service_parameters": {
                    "route": "AbnB2b",
                    "article": [
                        {"Description": "Widget", "Quantity": "2", "GrossUnitPrice": "125.00"},
                    ],
                    "billingCustomer": [billing],
                    "shippingCustomer": [_customer()],
                },
            },
        ).authorize()
        print(
            f"   authorize: status.code={authorize_response.status.code.code}  "
            f"key={authorize_response.key}"
        )

        # Once the order is confirmed, capture the authorized amount using the
        # transaction key from the authorize response.
        capture_response = app.payments.create_payment(
            "in3",
            {
                "currency": "EUR",
                "amount": 250.00,
                "description": "in3 capture demo",
                "invoice": "IN3-AUTH-001",
            },
        ).capture(original_transaction_key=authorize_response.key, amount=250.00)
        print(f"   capture:   status.code={capture_response.status.code.code}")
    except Exception as e:
        print(f"   ❌ {e}")


def _customer() -> dict:
    """A minimal In3 customer using the exact Buckaroo field names."""
    return {
        "FirstName": "John",
        "LastName": "Doe",
        "Phone": "0612345678",
        "Email": "john@example.com",
        "Street": "Hoofdstraat",
        "StreetNumber": "1",
        "PostalCode": "1000AA",
        "City": "Amsterdam",
        "CountryCode": "NL",
    }


def main() -> None:
    print("BUCKAROO SDK — IN3 DEMOS")
    print("=" * 60)
    demo_pay()
    demo_authorize_capture()
    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
