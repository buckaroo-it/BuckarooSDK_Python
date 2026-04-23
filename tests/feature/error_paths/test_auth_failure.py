import pytest

from buckaroo.exceptions._authentication_error import AuthenticationError
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestAuthFailure:
    """Verify that 401 / 403 responses surface as AuthenticationError."""

    @pytest.mark.parametrize(
        "status,match,invoice",
        [
            (401, "store key and secret key", "INV-AUTH-001"),
            (403, "Access forbidden", "INV-AUTH-403"),
        ],
    )
    def test_auth_failure_raises_authentication_error(
        self, buckaroo, mock_strategy, status, match, invoice
    ):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction",
                {
                    "Key": None,
                    "Status": {
                        "Code": {"Code": 491, "Description": "Validation failure"},
                        "SubCode": {"Code": "S001", "Description": "Authentication failed"},
                        "DateTime": "2024-01-01T00:00:00",
                    },
                    "RequiredAction": None,
                    "Services": [],
                },
                status=status,
            )
        )

        with pytest.raises(AuthenticationError, match=match):
            buckaroo.payments.create_payment(
                "ideal",
                Helpers.standard_payload(
                    invoice=invoice,
                    description=f"Auth failure {status} test",
                ),
            ).pay()
