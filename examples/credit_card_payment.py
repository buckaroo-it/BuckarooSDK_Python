#!/usr/bin/env python3
"""
Credit card payment examples.

Covers:
  - Pay with encrypted card data  (most common server-side flow)
  - Pay with Hosted Fields token  (payWithToken)
  - Authorize then capture        (two-step flow)
  - Authorize then cancel         (cancelAuthorize)
  - Recurring payment             (payRecurrent)
  - Refund

The credit card service name is dynamic: it reflects the card brand
(visa, mastercard, amex, …).  Pass it in ``from_dict`` as ``'brand'``.

Run:
  BUCKAROO_STORE_KEY=... BUCKAROO_SECRET_KEY=... python examples/credit_card_payment.py
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


def base_builder(brand: str = "visa"):
    """Return a pre-filled credit card builder for the given brand."""
    return app.payments.create_payment("creditcard", {
        "brand":            brand,
        "currency":         "EUR",
        "amount":           49.99,
        "description":      "Order #2001",
        "invoice":          "INV-2001",
        "return_url":       f"{RETURN_BASE}/return",
        "return_url_cancel":f"{RETURN_BASE}/cancel",
        "return_url_error": f"{RETURN_BASE}/error",
        "return_url_reject":f"{RETURN_BASE}/reject",
    })


# ── 1. Pay with encrypted card data ──────────────────────────────────────────

def example_pay_encrypted(encrypted_card_data: str):
    """
    Standard server-side encrypted payment.

    The ``encryptedCardData`` string is produced by the Buckaroo JavaScript
    encryption library on the client side, then posted to your server.
    Your server passes it straight through — it never sees raw card numbers.
    """
    response = (
        base_builder()
        .add_parameter("encryptedCardData", encrypted_card_data)
        .payEncrypted()
    )
    print_response("Pay encrypted (Visa)", response)
    return response


# ── 2. Pay with Hosted Fields token ──────────────────────────────────────────

def example_pay_with_token(session_id: str):
    """
    Hosted Fields inline payment.

    The ``session_id`` comes from Buckaroo's Hosted Fields ``submitSession()``
    JavaScript call on your checkout page.  Pass it here; Buckaroo tokenises
    the card on its side.

    The response may include a ``RequiredAction`` for 3-D Secure authentication.
    """
    response = (
        base_builder()
        .add_parameter("sessionId", session_id)
        .payWithToken()
    )
    print_response("Pay with Hosted Fields token", response)
    return response


# ── 3. Authorize then capture (two-step) ─────────────────────────────────────

def example_authorize_and_capture(encrypted_card_data: str):
    """
    Reserve the funds at authorisation time; capture later (e.g. on dispatch).
    """
    builder = (
        base_builder()
        .add_parameter("encryptedCardData", encrypted_card_data)
    )

    # Step 1 — authorise (no money moves yet)
    auth_response = builder.authorize()
    print_response("Authorize", auth_response)

    auth_key = auth_response.transaction_key
    if not auth_key:
        print("  No transaction key returned — cannot capture.")
        return

    # Step 2 — capture (money moves now)
    capture_response = builder.capture(original_transaction_key=auth_key)
    print_response("Capture", capture_response)

    return capture_response


# ── 4. Authorize then cancel ──────────────────────────────────────────────────

def example_authorize_and_cancel(encrypted_card_data: str):
    """Release the reserved funds without charging the customer."""
    builder = (
        base_builder()
        .add_parameter("encryptedCardData", encrypted_card_data)
    )

    auth_response = builder.authorize()
    print_response("Authorize (to be cancelled)", auth_response)

    auth_key = auth_response.transaction_key
    if not auth_key:
        print("  No transaction key returned — cannot cancel.")
        return

    cancel_response = builder.cancelAuthorize(original_transaction_key=auth_key)
    print_response("Cancel authorize", cancel_response)

    return cancel_response


# ── 5. Recurring payment ──────────────────────────────────────────────────────

def example_pay_recurrent(original_transaction_key: str):
    """
    Charge a customer again using a stored token from a previous transaction.
    The original transaction must have been created with ``startRecurrent=true``.
    """
    response = (
        base_builder()
        .add_parameter("originalTransactionKey", original_transaction_key)
        .payRecurrent()
    )
    print_response("Recurring payment", response)
    return response


# ── 6. Refund ─────────────────────────────────────────────────────────────────

def example_refund(original_transaction_key: str):
    """Full refund of a captured or completed payment."""
    response = base_builder().refund(original_transaction_key=original_transaction_key)
    print_response("Refund", response)
    return response


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("CREDIT CARD PAYMENT EXAMPLES")
    print("=" * 55)

    # These values come from the client-side Buckaroo JS library.
    # Replace them with real values from your test environment.
    ENCRYPTED_CARD_DATA = "REPLACE_WITH_ENCRYPTED_CARD_DATA"
    HOSTED_FIELDS_SESSION = "REPLACE_WITH_SESSION_ID"
    EXISTING_TXN_KEY      = "REPLACE_WITH_REAL_TXN_KEY"

    example_pay_encrypted(ENCRYPTED_CARD_DATA)
    example_pay_with_token(HOSTED_FIELDS_SESSION)
    example_authorize_and_capture(ENCRYPTED_CARD_DATA)
    example_authorize_and_cancel(ENCRYPTED_CARD_DATA)
    example_pay_recurrent(EXISTING_TXN_KEY)
    example_refund(EXISTING_TXN_KEY)
