import pytest

from buckaroo.exceptions._authentication_error import AuthenticationError
from tests.support.mock_request import BuckarooMockRequest


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
            buckaroo.payments.create_payment("ideal", {
                "amount": 10.00,
                "currency": "EUR",
                "description": "Auth failure test",
                "invoice": "INV-AUTH-001",
                "return_url": "https://example.com/return",
                "return_url_cancel": "https://example.com/cancel",
                "return_url_error": "https://example.com/error",
                "return_url_reject": "https://example.com/reject",
            }).pay()

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
            buckaroo.payments.create_payment("ideal", {
                "amount": 10.00,
                "currency": "EUR",
                "description": "Auth failure 403 test",
                "invoice": "INV-AUTH-403",
                "return_url": "https://example.com/return",
                "return_url_cancel": "https://example.com/cancel",
                "return_url_error": "https://example.com/error",
                "return_url_reject": "https://example.com/reject",
            }).pay()
