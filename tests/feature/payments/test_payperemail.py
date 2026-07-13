"""Feature test: PayPerEmail PaymentInvitation round-trip through the full stack.

Pay Per Email emails the shopper a payment link instead of returning an inline
redirect. The ``PaymentInvitation`` action carries the customer identity as
service parameters; this pins that the action and those params reach the wire.
"""

from tests.support.helpers import Helpers
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_service_parameters


class TestPayPerEmailFeature:
    def test_payment_invitation_sends_action_and_customer_params(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {"Name": "payperemail", "Action": "PaymentInvitation", "Parameters": []}
                ],
                "ServiceCode": "payperemail",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = buckaroo.payments.create_payment(
            "payperemail",
            Helpers.standard_payload(
                invoice="INV-PPE-001",
                description="Pay per email invite",
                service_parameters={
                    "CustomerEmail": "jane@example.com",
                    "CustomerFirstName": "Jane",
                    "CustomerLastName": "Doe",
                    "CustomerGender": "1",
                },
            ),
        ).execute_action("PaymentInvitation")

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert recorded_action(mock_strategy) == "PaymentInvitation"

        sent = {p["Name"].lower(): p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert sent["customeremail"] == "jane@example.com"
        assert sent["customerfirstname"] == "Jane"
        assert sent["customerlastname"] == "Doe"
        assert sent["customergender"] == "1"
