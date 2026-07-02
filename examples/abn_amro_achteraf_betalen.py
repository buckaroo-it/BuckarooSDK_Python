#!/usr/bin/env python3
"""Demo of ABN-AMRO Achteraf Betalen via the In3 payment method.

Same underlying service as In3 V3 — setting the optional ``Route`` service
parameter to ``abn_b2b`` selects ABN-AMRO Achteraf Betalen instead of the
default In3 acquirer. NL/B2B only. Gated on ``BUCKAROO_STORE_KEY`` /
``BUCKAROO_SECRET_KEY`` env vars.
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


def demo_abn_amro_achteraf_betalen() -> None:
    """Pay via In3 with the ABN-AMRO Achteraf Betalen route."""
    print("\nABN-AMRO Achteraf Betalen (In3, Route=abn_b2b)")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()

        # create_payment(method, params) dispatches through the PaymentMethodFactory
        # and returns a ready-to-execute In3Builder.
        builder = app.payments.create_payment(
            "in3",
            {
                "currency": "EUR",
                "amount": 121.00,
                "description": "ABN-AMRO Achteraf Betalen demo",
                "invoice": "ABN-B2B-DEMO-001",
                "return_url": "https://www.buckaroo.nl",
                "return_url_cancel": "https://www.buckaroo.nl/cancel",
                "return_url_error": "https://www.buckaroo.nl/error",
                "return_url_reject": "https://www.buckaroo.nl/reject",
                "service_parameters": {
                    "billingCustomer": [
                        {
                            "firstName": "John",
                            "lastName": "Doe",
                            "chamberOfCommerce": "12345678",
                            "companyName": "Acme B.V.",
                        }
                    ],
                    "shippingCustomer": [
                        {
                            "firstName": "John",
                            "lastName": "Doe",
                            "chamberOfCommerce": "12345678",
                            "companyName": "Acme B.V.",
                        }
                    ],
                    "article": [
                        {"description": "Widget", "quantity": "1", "price": "100.00"},
                    ],
                },
            },
        )

        # Route is optional and NL/B2B only - selects ABN-AMRO Achteraf Betalen
        # instead of the default In3 acquirer.
        builder.add_parameter("route", "abn_b2b")

        response = builder.pay()

        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — ABN-AMRO ACHTERAF BETALEN DEMO")
    print("=" * 60)
    print("Env vars read:")
    print("  BUCKAROO_STORE_KEY, BUCKAROO_SECRET_KEY, BUCKAROO_MODE")

    demo_abn_amro_achteraf_betalen()

    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
