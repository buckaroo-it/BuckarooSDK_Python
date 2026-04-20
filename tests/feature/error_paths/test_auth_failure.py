import pytest

from buckaroo.exceptions._authentication_error import AuthenticationError
from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestAuthFailure:
    """Verify that a 401 response from the API surfaces as AuthenticationError."""

    def test_auth_failure_raises_authentication_error(self, buckaroo, mock_strategy):
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", {
            "Key": None,
            "Status": {
                "Code": {"Code": 491, "Description": "Validation failure"},
                "SubCode": {"Code": "S001", "Description": "Authentication failed"},
                "DateTime": "2024-01-01T00:00:00",
            },
            "RequiredAction": None,
            "Services": [],
        }, status=401))

        with pytest.raises(AuthenticationError, match="store key and secret key"):
            buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
                invoice="INV-AUTH-001",
                description="Auth failure test",
            )).pay()

    def test_auth_failure_403_raises_authentication_error(self, buckaroo, mock_strategy):
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", {
            "Key": None,
            "Status": {
                "Code": {"Code": 491, "Description": "Validation failure"},
                "SubCode": {"Code": "S001", "Description": "Authentication failed"},
                "DateTime": "2024-01-01T00:00:00",
            },
            "RequiredAction": None,
            "Services": [],
        }, status=403))

        with pytest.raises(AuthenticationError, match="Access forbidden"):
            buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
                invoice="INV-AUTH-403",
                description="Auth failure 403 test",
            )).pay()
