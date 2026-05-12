"""Tests for HTTP 5xx server error handling."""

import pytest

from buckaroo.http.client import BuckarooApiError
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


def _error_body():
    return {
        "Status": {
            "Code": {"Code": 492, "Description": "Technical failure"},
            "SubCode": None,
            "DateTime": "2024-01-01T00:00:00",
        },
    }


class TestServerError:
    """Verify that 5xx responses raise BuckarooApiError with response attached."""

    @pytest.mark.parametrize(
        "status,body,invoice",
        [
            (500, _error_body(), "TEST-500"),
            (502, {}, "TEST-502"),
        ],
    )
    def test_5xx_response_raises_api_error(self, buckaroo, mock_strategy, status, body, invoice):
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", body, status=status)
        )

        with pytest.raises(BuckarooApiError, match=str(status)) as exc_info:
            buckaroo.payments.create_payment(
                "ideal",
                Helpers.standard_payload(
                    invoice=invoice,
                    description=f"Server error {status} test",
                ),
            ).pay()

        err = exc_info.value
        assert err.status_code == status
        assert err.response is not None

    def test_500_response_is_not_successful(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", _error_body(), status=500)
        )

        with pytest.raises(BuckarooApiError) as exc_info:
            buckaroo.payments.create_payment(
                "ideal",
                Helpers.standard_payload(
                    invoice="TEST-500-SUCCESS",
                    description="Success flag test",
                ),
            ).pay()

        assert exc_info.value.response.success is False
        assert exc_info.value.response.status_code == 500
