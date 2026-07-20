"""Feature test: POS (Point of Sale) pay round-trip through the full stack.

POS is a PIN-based in-store payment routed to a physical terminal via
``TerminalID``. The initial response is a pending/awaiting status — the
final result (plus the printable ``Ticket`` receipt) arrives later via push.
This pins the ``Pay`` action reaching the wire with the fixed ``Channel:
"Web"`` field and the ``TerminalID`` service parameter, and that the mock's
pending response round-trips through ``PaymentResponse``.

``terminal_id()`` is used (not the generic ``service_parameters`` dict) so
the ``TerminalID`` name reaches the wire with the exact casing Buckaroo
documents — ``add_parameter``'s generic ``.capitalize()`` would otherwise
mangle it to ``Terminalid``.
"""

import pytest

from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError
from tests.support.helpers import Helpers
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_service_parameters


_TERMINAL_ID = "50000001"


def _pos_payload(**overrides):
    payload = {
        "currency": "EUR",
        "amount": 0.01,
        "invoice": "TestFactuur01",
    }
    payload.update(overrides)
    return payload


class TestPosFeature:
    def test_pay_sends_channel_web_and_terminal_id(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "pospayment",
                        "Action": "Pay",
                        "Parameters": [{"Name": "TerminalID", "Value": _TERMINAL_ID}],
                    }
                ],
                "ServiceCode": "pospayment",
                "Invoice": "TestFactuur01",
                "TransactionType": "V735",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = (
            buckaroo.payments.create_payment("pospayment", _pos_payload())
            .terminal_id(_TERMINAL_ID)
            .pay()
        )

        assert response.key == response_body["Key"]
        assert response.status.code.code == 190
        assert response.service_code == "pospayment"

        assert recorded_action(mock_strategy) == "Pay"

        sent = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert sent["TerminalID"] == _TERMINAL_ID

    def test_pay_returns_pending_until_terminal_confirms(self, buckaroo, mock_strategy):
        """Initial response can carry an awaiting-consumer status; final result
        and the printable Ticket only arrive later via push."""
        response_body = Helpers.success_response(
            {
                "Status": {
                    "Code": {"Code": 792, "Description": "Waiting on customer input"},
                },
                "Services": [],
                "ServiceCode": "pospayment",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = (
            buckaroo.payments.create_payment("pospayment", _pos_payload())
            .terminal_id(_TERMINAL_ID)
            .pay()
        )

        assert response.is_pending() is True

    def test_pos_case_insensitive_lookup(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response({"ServiceCode": "pospayment"})
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = (
            buckaroo.payments.create_payment("POSPAYMENT", _pos_payload(invoice="INV-POS-CASE"))
            .terminal_id(_TERMINAL_ID)
            .pay()
        )

        assert response.status.code.code == 190

    def test_missing_terminal_id_raises(self, buckaroo, mock_strategy):
        builder = buckaroo.payments.create_payment("pospayment", _pos_payload())

        with pytest.raises(RequiredParameterMissingError):
            builder.pay()

    def test_blank_terminal_id_raises(self, buckaroo):
        builder = buckaroo.payments.create_payment("pospayment", _pos_payload())

        with pytest.raises(ValueError, match="non-empty"):
            builder.terminal_id("")

    def test_pospayment_is_available(self, buckaroo):
        assert buckaroo.payments.is_method_supported("pospayment")
