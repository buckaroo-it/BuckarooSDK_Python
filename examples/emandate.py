#!/usr/bin/env python3
"""Demo of the eMandate solution (B2C ``emandate`` + B2B ``emandateb2b``).

eMandate is a DataRequest-based solution for managing SEPA direct debit
mandates: list issuers, create a mandate, check its status, modify it, and
cancel it. The retail (B2C, service ``emandate``) and business (B2B, service
``emandateb2b``) variants share the same five actions; only the service name
differs. Each demo below runs against both variants. Gated on
``BUCKAROO_STORE_KEY`` / ``BUCKAROO_SECRET_KEY`` env vars.
"""

import os
import sys

# Add parent directory to Python path so the demo can import the SDK in-place.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo

SERVICES = ("emandate", "emandateb2b")


def _have_credentials() -> bool:
    if not os.getenv("BUCKAROO_STORE_KEY") or not os.getenv("BUCKAROO_SECRET_KEY"):
        print("⚠️  Set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY to run this demo")
        return False
    return True


def demo_issuer_list() -> None:
    """List available eMandate issuers via GetIssuerList (no parameters)."""
    print("\n1. Issuer list")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    for service in SERVICES:
        try:
            response = app.solutions.create_solution(service).issuer_list()
            print(f"   [{service}] status.code={response.status.code.code}  key={response.key}")
        except Exception as e:
            print(f"   [{service}] ❌ {e}")


def demo_create_mandate() -> None:
    """Create a mandate via CreateMandate. Only ``debtorReference`` is required."""
    print("\n2. Create mandate")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    for service in SERVICES:
        try:
            response = app.solutions.create_solution(
                service,
                {
                    "service_parameters": {
                        "debtorReference": "DEBTOR-DEMO-001",
                        "debtorBankId": "ABNANL2A",
                        "sequenceType": "1",
                        "purchaseId": "EMANDATE-DEMO-001",
                        "language": "nl",
                    }
                },
            ).create_mandate()
            mandate_id = response.get_service_parameter("MandateId")
            print(f"   [{service}] status.code={response.status.code.code}  mandateId={mandate_id}")
        except Exception as e:
            print(f"   [{service}] ❌ {e}")


def demo_status() -> None:
    """Look up a mandate's status via GetStatus. ``mandateId`` is required."""
    print("\n3. Mandate status")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    for service in SERVICES:
        try:
            response = app.solutions.create_solution(
                service,
                {"service_parameters": {"mandateId": "MND-DEMO-001"}},
            ).status()
            mandate_status = response.get_service_parameter("Status")
            print(
                f"   [{service}] status.code={response.status.code.code}  mandateStatus={mandate_status}"
            )
        except Exception as e:
            print(f"   [{service}] ❌ {e}")


def demo_modify_mandate() -> None:
    """Modify a mandate via ModifyMandate. ``mandateId`` is required."""
    print("\n4. Modify mandate")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    for service in SERVICES:
        try:
            response = app.solutions.create_solution(
                service,
                {
                    "service_parameters": {
                        "mandateId": "MND-DEMO-001",
                        "maxAmount": "1000.00",
                    }
                },
            ).modify_mandate()
            print(f"   [{service}] status.code={response.status.code.code}  key={response.key}")
        except Exception as e:
            print(f"   [{service}] ❌ {e}")


def demo_cancel_mandate() -> None:
    """Cancel a mandate via CancelMandate. ``mandateId`` is required."""
    print("\n5. Cancel mandate")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    for service in SERVICES:
        try:
            response = app.solutions.create_solution(
                service,
                {
                    "service_parameters": {
                        "mandateId": "MND-DEMO-001",
                        "purchaseId": "EMANDATE-DEMO-001",
                    }
                },
            ).cancel_mandate()
            print(f"   [{service}] status.code={response.status.code.code}  key={response.key}")
        except Exception as e:
            print(f"   [{service}] ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — EMANDATE DEMO")
    print("=" * 60)

    demo_issuer_list()
    demo_create_mandate()
    demo_status()
    demo_modify_mandate()
    demo_cancel_mandate()

    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
