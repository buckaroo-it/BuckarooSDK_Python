#!/usr/bin/env python3
"""
Point of Sale (POS) payment examples.

POS transactions are PIN-based in-store payments processed through a
physical payment terminal. You initiate the transaction via API with the
terminal's unique ``TerminalID``; Buckaroo routes the request to that
terminal, which prompts the customer to complete payment there. Every POS
request is sent with a fixed ``Channel: "Web"`` — the SDK sets this
internally, it is not configurable.

The immediate response carries a pending/awaiting status. The final result,
plus the printable ``Ticket`` receipt text for the customer, arrives later
via push notification — this demo also shows how to parse that push body.

Covers:
  - Pay (initiate a transaction at a terminal)
  - Parsing a push notification, including the printable Ticket data

Run:
  BUCKAROO_STORE_KEY=... BUCKAROO_SECRET_KEY=... python examples/pos_payment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo
from buckaroo.models.payment_response import BuckarooStatusCode, PaymentResponse

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
    print(f"  Pending       : {response.is_pending()}")
    if response.transaction_key:
        print(f"  Txn key       : {response.transaction_key}")


def base_builder():
    """Return a pre-filled POS builder ready to customise.

    No return URLs are needed — POS has no redirect flow, the customer pays
    directly at the terminal.
    """
    return (
        app.payments.create_payment("pospayment")
        .currency("EUR")
        .amount(0.01)
        .invoice("TestFactuur01")
    )


# ── 1. Pay — initiate a transaction at a terminal ────────────────────────────

def example_pay(terminal_id: str = "50000001"):
    """
    Initiate a POS transaction through the given terminal.

    Buckaroo routes the request to the terminal, which prompts the customer
    for their PIN. The response here is only the initial acknowledgement —
    the actual payment result arrives later via push (see
    ``example_parse_push`` below).
    """
    response = base_builder().terminal_id(terminal_id).pay()
    print_response("Pay — POS terminal transaction", response)
    return response


# ── 2. Parse a push notification, including the printable Ticket ────────────

# Buckaroo POSTs this JSON to your configured push URL once the terminal
# transaction completes. In a real application this is the raw body your
# webhook endpoint receives — this constant just stands in for that so the
# demo is runnable without a live terminal.
_EXAMPLE_PUSH_BODY = {
    "Transaction": {
        "Key": "8D2EAFC8F76D40FEBA204AFB53Fxxxxx",
        "Invoice": "TestFactuur01",
        "ServiceCode": "pospayment",
        "Status": {
            "Code": {"Code": 190, "Description": "Success"},
            "SubCode": {"Code": "S001", "Description": "Transaction successfully processed"},
            "DateTime": "2020-02-18T15:00:11",
        },
        "Currency": "EUR",
        "AmountDebit": 0.01,
        "Services": [
            {
                "Name": "PosPayment",
                "Parameters": [
                    {
                        "Name": "Ticket",
                        "Value": (
                            "[0]POI: 50000001\r\n"
                            "[0]KLANTTICKET\r\n"
                            "[0]------------------------------------------------\r\n"
                        ),
                    }
                ],
            }
        ],
    }
}


def example_parse_push(push_body: dict = _EXAMPLE_PUSH_BODY):
    """
    Parse an incoming POS push notification.

    Push bodies wrap the transaction under a top-level ``Transaction`` key —
    unwrap it, then feed it to :class:`PaymentResponse` the same way the SDK
    does for a direct API response (under a ``data`` key).

    Note: ``is_successful()`` relies on a convenience flag that only
    ``BuckarooResponse`` (the HTTP-layer wrapper) sets, so it doesn't apply
    to a ``PaymentResponse`` built directly from a push body — compare the
    status code instead, as below.
    """
    transaction = push_body["Transaction"]
    response = PaymentResponse({"data": transaction})
    successful = bool(response.status) and response.status.code.code == BuckarooStatusCode.SUCCESS

    print(f"\n{'─' * 55}")
    print("  Push notification — POS transaction complete")
    print(f"{'─' * 55}")
    print(f"  Txn key    : {response.key}")
    print(f"  Status     : {response.status.code.code} — {response.status.code.description}")
    print(f"  Successful : {successful}")

    ticket = response.get_service_parameter("Ticket")
    if ticket:
        print("  Ticket (printable receipt):")
        print("  " + "-" * 40)
        for line in ticket.splitlines():
            print(f"  {line}")
        print("  " + "-" * 40)

    return response


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("POS (POINT OF SALE) PAYMENT EXAMPLES")
    print("=" * 55)

    example_pay()
    example_parse_push()
