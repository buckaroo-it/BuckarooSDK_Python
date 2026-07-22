#!/usr/bin/env python3
"""Demo of the Credit Management solution (``creditmanagement``, service ``CreditManagement3``).

Credit Management is a DataRequest-based solution for invoicing and debtor
administration: create invoices, manage debtors, run payment plans, and pause
or look up invoices and debtor files. ``create_combined_invoice`` is the
exception — it builds a supplementary service that is *combined* into a
funding payment or refund, like Split Payments. Gated on
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


def demo_create_invoice() -> None:
    """Create an invoice via CreateInvoice.

    ``invoice`` and ``currency`` are TOP-LEVEL request fields, not service
    parameters — the gateway rejects them as service params with
    ``ParameterMissing``. ``schemeKey`` must belong to the same store as your
    store key; ``txnpk6`` below is the demo account's scheme — replace it with
    your own from Plaza. ``debtor.code`` is required.
    """
    print("\n1. Create invoice")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution(
            "creditmanagement",
            {
                "invoice": "INV-DEMO-001",
                "currency": "EUR",
                "service_parameters": {
                    "invoiceAmount": "250.00",
                    "dueDate": "2026-09-01",
                    "schemeKey": "txnpk6",
                    "debtor": {"code": "DEBTOR-DEMO-001"},
                },
            },
        ).create_invoice()
        invoice_key = response.get_service_parameter("InvoiceKey")
        print(f"   status.code={response.status.code.code}  invoiceKey={invoice_key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_create_combined_invoice() -> None:
    """CreateCombinedInvoice: build the invoice, combine it into an iDEAL payment.

    The combined request has a single shared top level, so ``invoice`` and
    ``currency`` are set on the *funding* iDEAL payment below, not on the
    CreditManagement3 sub-builder.
    """
    print("\n2. Create combined invoice")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        cm = app.solutions.create_solution(
            "creditmanagement",
            {
                "service_parameters": {
                    "invoiceAmount": "95.00",
                    "dueDate": "2026-09-01",
                    "schemeKey": "txnpk6",
                    "debtor": {"code": "DEBTOR-DEMO-001"},
                }
            },
        ).create_combined_invoice()

        response = (
            app.payments.create_payment(
                "ideal",
                {
                    "currency": "EUR",
                    "amount": 95.00,
                    "invoice": "INV-DEMO-002",
                    "description": "Combined invoice order INV-DEMO-002",
                    "service_parameters": {"issuer": "ABNANL2A"},
                    "return_url": "https://example.com/return",
                    "return_url_cancel": "https://example.com/cancel",
                    "return_url_error": "https://example.com/error",
                    "return_url_reject": "https://example.com/reject",
                },
            )
            .combine(cm)
            .pay()
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_add_or_update_debtor() -> None:
    """Create or update a debtor via AddOrUpdateDebtor with grouped debtor details."""
    print("\n3. Add or update debtor")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution(
            "creditmanagement",
            {
                "service_parameters": {
                    "debtor": {"code": "DEBTOR-DEMO-001"},
                    "person": {"firstName": "John", "lastName": "Doe"},
                    "address": {"street": "Main St", "city": "Amsterdam"},
                    "email": {"email": "john@example.com"},
                }
            },
        ).add_or_update_debtor()
        debtor_key = response.get_service_parameter("DebtorKey")
        print(f"   status.code={response.status.code.code}  debtorKey={debtor_key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_debtor_info() -> None:
    """Look up a debtor via DebtorInfo. ``debtor.code`` is required."""
    print("\n4. Debtor info")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"debtor": {"code": "DEBTOR-DEMO-001"}}},
        ).debtor_info()
        status = response.get_service_parameter("Status")
        print(f"   status.code={response.status.code.code}  debtorStatus={status}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_add_or_update_product_lines() -> None:
    """Add product lines via AddOrUpdateProductLines.

    Articles must be passed as the ``articles`` method argument, not through
    ``service_parameters`` — the latter builds a wrong ``Articles`` group.
    Each article requires ``type`` (``"Regular"`` for a normal line),
    ``totalAmount`` and ``totalVat`` on top of the usual fields.
    """
    print("\n5. Add or update product lines")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        builder = app.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"invoiceKey": "INVK-DEMO-001"}},
        )
        response = builder.add_or_update_product_lines(
            articles=[
                {
                    "identifier": "SKU-1",
                    "description": "Widget",
                    "quantity": "2",
                    "price": "10.00",
                    "type": "Regular",
                    "totalAmount": "20.00",
                    "totalVat": "4.20",
                    "vatPercentage": "21",
                },
            ]
        )
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_create_payment_plan() -> None:
    """Create a payment plan via CreatePaymentPlan.

    ``description`` is a TOP-LEVEL request field, not a service parameter —
    the gateway rejects it as an unknown parameter when sent as one.

    Requires an active Buckaroo Credit Management subscription on the
    account and an included invoice that is past its due date — the gateway
    enforces these, not the SDK.
    """
    print("\n6. Create payment plan")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution(
            "creditmanagement",
            {
                "description": "3-month plan",
                "service_parameters": {
                    "includedInvoiceKey": "INVK-DEMO-001",
                    "dossierNumber": "DOSSIER-DEMO-001",
                    "startDate": "2026-09-01",
                    "interval": "Month",
                    "paymentPlanCostAmount": "5.00",
                    "recipientEmail": "debtor@example.com",
                    "installmentCount": "3",
                },
            },
        ).create_payment_plan()
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_invoice_info() -> None:
    """Look up an invoice via InvoiceInfo.

    ``invoice`` is a TOP-LEVEL request field, not a service parameter.
    """
    print("\n7. Invoice info")
    print("-" * 40)
    if not _have_credentials():
        return

    app = Buckaroo.from_env()
    try:
        response = app.solutions.create_solution(
            "creditmanagement", {"invoice": "INV-DEMO-001"}
        ).invoice_info()
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — CREDIT MANAGEMENT DEMO")
    print("=" * 60)

    demo_create_invoice()
    demo_create_combined_invoice()
    demo_add_or_update_debtor()
    demo_debtor_info()
    demo_add_or_update_product_lines()
    demo_create_payment_plan()
    demo_invoice_info()

    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
