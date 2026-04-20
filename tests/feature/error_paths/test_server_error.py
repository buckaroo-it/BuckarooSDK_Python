"""Tests for HTTP 500 server error handling."""

import pytest

from buckaroo.http.client import BuckarooApiError
from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestServerError:
    """Verify that 500 responses raise BuckarooApiError with response attached."""

    def test_500_response_raises_api_error(self, buckaroo, mock_strategy):
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", {
            "Status": {
                "Code": {"Code": 492, "Description": "Technical failure"},
                "SubCode": None,
                "DateTime": "2024-01-01T00:00:00",
            },
        }, status=500))

        with pytest.raises(BuckarooApiError, match="500") as exc_info:
            buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
                invoice="TEST-500",
                description="Server error test",
            )).pay()

        err = exc_info.value
        assert err.status_code == 500
        assert err.response is not None

    def test_500_response_is_not_successful(self, buckaroo, mock_strategy):
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", {
            "Status": {
                "Code": {"Code": 492, "Description": "Technical failure"},
                "SubCode": None,
                "DateTime": "2024-01-01T00:00:00",
            },
        }, status=500))

        with pytest.raises(BuckarooApiError) as exc_info:
            buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
                invoice="TEST-500-SUCCESS",
                description="Success flag test",
            )).pay()

        assert exc_info.value.response.success is False
        assert exc_info.value.response.status_code == 500

    def test_502_gateway_error(self, buckaroo, mock_strategy):
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", {}, status=502))

        with pytest.raises(BuckarooApiError, match="502"):
            buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
                invoice="TEST-502",
                amount=5.00,
                description="Gateway error test",
            )).pay()
