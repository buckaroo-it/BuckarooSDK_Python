#!/usr/bin/env python3
"""Demo of the Buckaroo app wrapper.

Shows the four supported ways to construct ``Buckaroo`` and drive a payment
through ``PaymentService`` / ``SolutionService``. All demos are gated on
``BUCKAROO_STORE_KEY`` / ``BUCKAROO_SECRET_KEY`` env vars.
"""

import os
import sys

# Add parent directory to Python path so the demo can import the SDK in-place.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buckaroo.app import Buckaroo, BuckarooConfig
from buckaroo.observers import LogDestination, LogLevel


def _have_credentials() -> bool:
    if not os.getenv("BUCKAROO_STORE_KEY") or not os.getenv("BUCKAROO_SECRET_KEY"):
        print("⚠️  Set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY to run this demo")
        return False
    return True


def demo_quick_setup() -> None:
    """Minimal bootstrap: one call, ready to go."""
    print("\n1. Quick setup")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.quick_setup(
            store_key=os.environ["BUCKAROO_STORE_KEY"],
            secret_key=os.environ["BUCKAROO_SECRET_KEY"],
            mode="test",
        )
        app.log_info("quick setup demo started")

        # Drive a subscription via the solutions service. SolutionBuilder.createSubscription
        # returns a PaymentResponse with the pending-redirect contract.
        solution = app.solutions.create({"method": "subscription"})
        response = solution.createSubscription(validate=False)

        print(f"   status.code={response.status.code.code}  key={response.key}")
        app.log_info("quick setup demo finished")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_from_env() -> None:
    """Construct Buckaroo from the ``BUCKAROO_*`` environment variables."""
    print("\n2. Environment config (Buckaroo.from_env)")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        app = Buckaroo.from_env()
        app.log_info("env-config demo started")

        # create_payment(method, params) dispatches through the PaymentMethodFactory
        # and returns a ready-to-execute PaymentBuilder.
        builder = app.payments.create_payment(
            "ideal",
            {
                "currency": "EUR",
                "amount": 15.75,
                "description": "env-config demo",
                "invoice": "ENV-DEMO-001",
                "return_url": "https://www.buckaroo.nl",
                "return_url_cancel": "https://www.buckaroo.nl/cancel",
                "return_url_error": "https://www.buckaroo.nl/error",
                "return_url_reject": "https://www.buckaroo.nl/reject",
                "service_parameters": {"issuer": "ABNANL2A"},
            },
        )
        response = builder.pay()

        print(f"   is_pending={response.is_pending()}  redirect={response.get_redirect_url()}")
        app.log_info("env-config demo finished")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_custom_config() -> None:
    """Construct Buckaroo with a hand-built ``BuckarooConfig``."""
    print("\n3. Custom config")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        config = BuckarooConfig(
            store_key=os.environ["BUCKAROO_STORE_KEY"],
            secret_key=os.environ["BUCKAROO_SECRET_KEY"],
            mode="test",
            enable_logging=True,
            log_level=LogLevel.DEBUG,
            log_destination=LogDestination.STDOUT,
            mask_sensitive_data=True,
            timeout=45,
            retry_attempts=5,
        )
        app = Buckaroo(config)

        # create_child_logger adds structured context to every subsequent log line.
        child = app.create_child_logger({"session_id": "sess_custom_001", "demo": "custom_config"})
        if child:
            child.log_info("payment flow started with session context")

        builder = app.payments.create_payment(
            "ideal",
            {
                "currency": "EUR",
                "amount": 42.00,
                "description": "custom-config demo",
                "invoice": "CUSTOM-001",
                "return_url": "https://www.buckaroo.nl",
                "return_url_cancel": "https://www.buckaroo.nl/cancel",
                "return_url_error": "https://www.buckaroo.nl/error",
                "return_url_reject": "https://www.buckaroo.nl/reject",
                "service_parameters": {"issuer": "ABNANL2A"},
            },
        )
        response = builder.pay()
        print(f"   status.code={response.status.code.code}  key={response.key}")
    except Exception as e:
        print(f"   ❌ {e}")


def demo_context_manager() -> None:
    """``Buckaroo`` supports ``with`` — logs entry + exit automatically."""
    print("\n4. Context manager")
    print("-" * 40)
    if not _have_credentials():
        return

    try:
        with Buckaroo.quick_setup(
            store_key=os.environ["BUCKAROO_STORE_KEY"],
            secret_key=os.environ["BUCKAROO_SECRET_KEY"],
        ) as app:
            app.log_info("context-manager demo started")

            for i in range(2):
                builder = app.payments.create_payment(
                    "ideal",
                    {
                        "currency": "EUR",
                        "amount": 10.00 + i,
                        "description": f"ctx demo {i + 1}",
                        "invoice": f"CTX-{i + 1:03d}",
                        "return_url": "https://www.buckaroo.nl",
                        "return_url_cancel": "https://www.buckaroo.nl/cancel",
                        "return_url_error": "https://www.buckaroo.nl/error",
                        "return_url_reject": "https://www.buckaroo.nl/reject",
                        "service_parameters": {"issuer": "ABNANL2A"},
                    },
                )
                response = builder.pay()
                app.log_info(f"payment {i + 1} dispatched", code=response.status.code.code)
    except Exception as e:
        print(f"   ❌ {e}")


def main() -> None:
    print("BUCKAROO SDK — APP WRAPPER DEMOS")
    print("=" * 60)
    print("Env vars read by BuckarooConfig.from_env():")
    print("  BUCKAROO_STORE_KEY, BUCKAROO_SECRET_KEY, BUCKAROO_MODE")
    print("  BUCKAROO_LOG_LEVEL={DEBUG|INFO|WARNING|ERROR}")
    print("  BUCKAROO_LOG_DESTINATION={stdout|file|both}")
    print("  BUCKAROO_LOG_FILE=/path/to/log")
    print("  BUCKAROO_LOG_MASK_SENSITIVE={true|false}")
    print("  BUCKAROO_TIMEOUT, BUCKAROO_RETRY_ATTEMPTS")

    demo_quick_setup()
    demo_from_env()
    demo_custom_config()
    demo_context_manager()

    print("\n" + "=" * 60)
    print("done.")


if __name__ == "__main__":
    main()
