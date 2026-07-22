"""Feature test: iDIN identify/verify/login round-trip through the full stack.

Every iDIN action is a DataRequest carrying a single ``issuerId`` service
parameter (BIC code of the consumer's bank); the sandbox issuer is
``BANKNL2Y``. The immediate response only carries the redirect — bank
personal data arrives later via push — so this pins the action name, the
``issuerId`` reaching the wire, and ``response.key`` parsing from the mock.
"""

from tests.support.helpers import Helpers
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_service_parameters

_ISSUER_ID = "BANKNL2Y"


def _idin_payload(**overrides):
    payload = {
        "return_url": "https://example.com/return",
        "return_url_cancel": "https://example.com/cancel",
        "return_url_error": "https://example.com/error",
        "return_url_reject": "https://example.com/reject",
        "service_parameters": {"issuerId": _ISSUER_ID},
    }
    payload.update(overrides)
    return payload


class TestIdinFeature:
    def test_identify_sends_action_and_issuer_id(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": "Idin", "Action": "identify", "Parameters": []}],
                "ServiceCode": "IDIN",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.payments.create_payment("idin", _idin_payload()).identify()

        assert response.key == response_body["Key"]
        assert recorded_action(mock_strategy) == "identify"

        sent = {p["Name"].lower(): p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert sent["issuerid"] == _ISSUER_ID

    def test_verify_sends_action_and_issuer_id(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": "Idin", "Action": "verify", "Parameters": []}],
                "ServiceCode": "IDIN",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.payments.create_payment("idin", _idin_payload()).verify()

        assert response.key == response_body["Key"]
        assert recorded_action(mock_strategy) == "verify"

        sent = {p["Name"].lower(): p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert sent["issuerid"] == _ISSUER_ID

    def test_login_sends_action_and_issuer_id(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": "Idin", "Action": "login", "Parameters": []}],
                "ServiceCode": "IDIN",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.payments.create_payment("idin", _idin_payload()).login()

        assert response.key == response_body["Key"]
        assert recorded_action(mock_strategy) == "login"

        sent = {p["Name"].lower(): p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert sent["issuerid"] == _ISSUER_ID
