#!/usr/bin/env python3
"""Demo of the iDIN payment method.

iDIN lets Dutch banks confirm a consumer's identity on the merchant's behalf.
Every action is a DataRequest keyed on a single ``issuerId`` (BIC code of the
consumer's bank) service parameter; the sandbox issuer is ``BANKNL2Y``. The
demo drives all three actions: identify, verify (age 18+), and login. Gated
on ``BUCKAROO_STORE_KEY`` / ``BUCKAROO_SECRET_KEY`` env vars.
"""

import os
import sys

# Add parent directory to Python path so the demo can import the SDK in-place.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo

_ISSUER_ID = "BANKNL2Y"


def _have_credentials() -> bool:
    if not os.getenv("BUCKAROO_STORE_KEY") or not os.getenv("BUCKAROO_SECRET_KEY"):
        print("⚠️  Set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY to run this demo")
        return False
    return True


def _idin_payload() -> dict:
    # iDIN carries no amount/currency; only the ReturnURL family plus the
    # issuerId service parameter (BIC code of the consumer's bank).
    return {
        "return_url": "https://www.buckaroo.nl",
        "return_url_cancel": "https://www.buckaroo.nl/cancel",
        "return_url_error": "https://www.buckaroo.nl/error",
        "return_url_reject": "https://www.buckaroo.nl/reject",
        "service_parameters": {"issuerId": _ISSUER_ID},
    }


def demo_identify() -> None:
    """Request full identification from the consumer's bank."""
    print("\n1. iDIN identify")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()
        response = app.payments.create_payment("idin", _idin_payload()).identify()
        print(f"   status.code={response.status.code.code}  key={response.key}")
        print(f"   redirect={response.get_redirect_url()}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_verify() -> None:
    """Verify whether the consumer is 18 years or older."""
    print("\n2. iDIN verify (age 18+)")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()
        response = app.payments.create_payment("idin", _idin_payload()).verify()
        print(f"   status.code={response.status.code.code}  key={response.key}")
        print(f"   redirect={response.get_redirect_url()}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_login() -> None:
    """Request a unique consumer ID for login purposes."""
    print("\n3. iDIN login")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()
        response = app.payments.create_payment("idin", _idin_payload()).login()
        print(f"   status.code={response.status.code.code}  key={response.key}")
        print(f"   redirect={response.get_redirect_url()}")
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — IDIN DEMO")
    print("=" * 60)
    demo_identify()
    demo_verify()
    demo_login()
    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
