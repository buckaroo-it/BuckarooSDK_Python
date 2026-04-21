"""Tests for malformed (non-JSON) response handling."""

import json

import pytest

from buckaroo.http.client import BuckarooApiError, BuckarooResponse
from buckaroo.http.strategies.http_strategy import HttpResponse
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestMalformedResponse:
    """Verify that non-JSON response bodies raise BuckarooApiError."""

    def test_malformed_json_raises_error(self, buckaroo, mock_strategy):
        """A 200 response with non-JSON text triggers BuckarooApiError."""
        mock_strategy.queue(
            BuckarooMockRequest.text(
                "POST",
                "*/json/transaction",
                body="<html>not json at all</html>",
            )
        )

        with pytest.raises(BuckarooApiError, match="Failed to parse Buckaroo response JSON"):
            buckaroo.payments.create_payment(
                "ideal",
                Helpers.standard_payload(
                    invoice="TEST-MALFORMED",
                    description="Malformed JSON test",
                ),
            ).pay()

    def test_malformed_json_wraps_json_decode_error(self, buckaroo, mock_strategy):
        """The raised BuckarooApiError chains the original JSONDecodeError."""
        mock_strategy.queue(
            BuckarooMockRequest.text(
                "POST",
                "*/json/transaction",
                body="{truncated",
            )
        )

        with pytest.raises(BuckarooApiError) as exc_info:
            buckaroo.payments.create_payment(
                "ideal",
                Helpers.standard_payload(
                    invoice="TEST-CHAIN",
                    amount=5.00,
                    description="Chained exception test",
                ),
            ).pay()

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)

    def test_buckaroo_response_directly_with_garbage(self):
        """BuckarooResponse raises BuckarooApiError for non-JSON text."""
        http_resp = HttpResponse(
            status_code=200,
            headers={},
            text="THIS IS NOT JSON",
            success=True,
        )
        with pytest.raises(BuckarooApiError, match="Failed to parse Buckaroo response JSON"):
            BuckarooResponse(http_resp)

    @pytest.mark.parametrize("text", ["", "   ", "\n"])
    def test_empty_response_does_not_raise(self, text):
        """Empty or whitespace-only body is treated as empty dict, no error."""
        http_resp = HttpResponse(
            status_code=200,
            headers={},
            text=text,
            success=True,
        )
        resp = BuckarooResponse(http_resp)
        assert resp.data == {}
