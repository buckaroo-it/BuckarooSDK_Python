"""Unit tests for buckaroo.http.client.BuckarooResponse.

BuckarooResponse wraps an HttpResponse and exposes predicates/parsers for
Buckaroo-specific fields. These tests construct HttpResponse instances
directly — no HTTP client, no mocks.
"""

import pytest

from buckaroo.http.client import BuckarooResponse
from buckaroo.http.strategies.http_strategy import HttpResponse


def make_response(status_code=200, text="", headers=None, success=True):
    """Build an HttpResponse with sensible defaults."""
    return HttpResponse(
        status_code=status_code,
        headers=headers or {},
        text=text,
        success=success,
    )


class TestSuccessPredicate:
    @pytest.mark.parametrize(
        "status_code,expected",
        [
            (199, False),
            (200, True),
            (299, True),
            (300, False),
            (500, False),
        ],
    )
    def test_success_is_true_only_for_2xx(self, status_code, expected):
        response = BuckarooResponse(make_response(status_code=status_code))

        assert response.success is expected


class TestDataParsing:
    def test_parses_valid_json_body(self):
        response = BuckarooResponse(make_response(text='{"Key": "abc", "n": 7}'))

        assert response.data == {"Key": "abc", "n": 7}

    def test_empty_body_returns_empty_dict(self):
        response = BuckarooResponse(make_response(text=""))

        assert response.data == {}

    def test_invalid_json_raises_buckaroo_api_error(self):
        from buckaroo.http.client import BuckarooApiError

        with pytest.raises(BuckarooApiError):
            BuckarooResponse(make_response(text="not-json"))

    def test_json_alias_returns_same_data(self):
        response = BuckarooResponse(make_response(text='{"a": 1}'))

        assert response.json() == response.data

    def test_data_returns_empty_dict_when_parsed_value_is_falsy(self):
        # Force _data to a falsy value to hit the `or {}` branch in the getter.
        response = BuckarooResponse(make_response(text=""))
        response._data = None

        assert response.data == {}


class TestPassThroughAttributes:
    def test_status_code_passes_through(self):
        response = BuckarooResponse(make_response(status_code=418))

        assert response.status_code == 418

    def test_text_passes_through(self):
        response = BuckarooResponse(make_response(text='{"x": 1}'))

        assert response.text == '{"x": 1}'

    def test_headers_pass_through(self):
        headers = {"Content-Type": "application/json", "X-Trace": "abc"}
        response = BuckarooResponse(make_response(headers=headers))

        assert response.headers == headers


class TestIsSuccessfulPayment:
    def test_returns_false_when_http_failed(self):
        response = BuckarooResponse(
            make_response(status_code=500, text='{"Status": {"Code": 190}}')
        )

        assert response.is_successful_payment() is False

    @pytest.mark.parametrize("code", [190, 490, 491, 492, 790, 791, 792, 793])
    def test_true_for_each_buckaroo_success_code(self, code):
        response = BuckarooResponse(
            make_response(text=f'{{"Status": {{"Code": {code}}}}}')
        )

        assert response.is_successful_payment() is True

    def test_false_for_non_success_buckaroo_code(self):
        response = BuckarooResponse(
            make_response(text='{"Status": {"Code": 491000}}')
        )

        assert response.is_successful_payment() is False

    def test_handles_nested_code_dict_shape(self):
        response = BuckarooResponse(
            make_response(
                text='{"Status": {"Code": {"Code": 190, "Description": "Success"}}}'
            )
        )

        assert response.is_successful_payment() is True

    def test_returns_success_when_no_status_field(self):
        # HTTP 2xx but no "Status" in body — falls through to self.success.
        response = BuckarooResponse(make_response(text='{"Other": "field"}'))

        assert response.is_successful_payment() is True

    def test_false_when_status_code_missing_from_status(self):
        response = BuckarooResponse(make_response(text='{"Status": {"Other": 1}}'))

        # Status present but no "Code" key — falls through to self.success.
        assert response.is_successful_payment() is True

    def test_false_when_code_is_unknown_type(self):
        response = BuckarooResponse(
            make_response(text='{"Status": {"Code": "oops"}}')
        )

        assert response.is_successful_payment() is False

    def test_false_when_status_is_falsy(self):
        # Status present but falsy — skips the Buckaroo-code branch.
        response = BuckarooResponse(make_response(text='{"Status": null}'))

        assert response.is_successful_payment() is True

    def test_false_when_data_is_empty_but_http_ok(self):
        # No _data at all -> falls through to self.success.
        response = BuckarooResponse(make_response(text=""))

        assert response.is_successful_payment() is True


class TestGetStatusCode:
    def test_returns_simple_int_code(self):
        response = BuckarooResponse(
            make_response(text='{"Status": {"Code": 190}}')
        )

        assert response.get_status_code() == 190

    def test_flattens_nested_code_dict(self):
        response = BuckarooResponse(
            make_response(
                text='{"Status": {"Code": {"Code": 490, "Description": "Failed"}}}'
            )
        )

        assert response.get_status_code() == 490

    def test_returns_none_when_data_missing(self):
        response = BuckarooResponse(make_response(text=""))

        assert response.get_status_code() is None

    def test_returns_none_when_status_missing(self):
        response = BuckarooResponse(make_response(text='{"Other": 1}'))

        assert response.get_status_code() is None

    def test_returns_none_when_status_falsy(self):
        response = BuckarooResponse(make_response(text='{"Status": null}'))

        assert response.get_status_code() is None

    def test_returns_none_when_code_missing(self):
        response = BuckarooResponse(make_response(text='{"Status": {"Other": 1}}'))

        assert response.get_status_code() is None

    def test_returns_none_for_unknown_code_type(self):
        response = BuckarooResponse(
            make_response(text='{"Status": {"Code": "string-code"}}')
        )

        assert response.get_status_code() is None


class TestGetStatusMessage:
    def test_prefers_subcode_description(self):
        body = (
            '{"Status": {"Code": {"Description": "Code desc"}, '
            '"SubCode": {"Description": "Sub desc"}}}'
        )
        response = BuckarooResponse(make_response(text=body))

        assert response.get_status_message() == "Sub desc"

    def test_falls_back_to_code_description_when_subcode_none(self):
        body = '{"Status": {"Code": {"Description": "Code desc"}, "SubCode": null}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_status_message() == "Code desc"

    def test_empty_when_subcode_none_and_code_has_no_description(self):
        body = '{"Status": {"Code": {"Other": 1}, "SubCode": null}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_status_message() == ""

    def test_empty_when_subcode_none_and_code_is_int(self):
        body = '{"Status": {"Code": 190, "SubCode": null}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_status_message() == ""

    def test_empty_when_subcode_is_not_dict(self):
        # SubCode present but not a dict — falls through to trailing "".
        body = '{"Status": {"Code": 190, "SubCode": "not-a-dict"}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_status_message() == ""

    def test_subcode_dict_missing_description(self):
        body = '{"Status": {"Code": 190, "SubCode": {"Other": 1}}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_status_message() == ""

    def test_empty_when_data_missing(self):
        response = BuckarooResponse(make_response(text=""))

        assert response.get_status_message() == ""

    def test_empty_when_status_missing(self):
        response = BuckarooResponse(make_response(text='{"Other": 1}'))

        assert response.get_status_message() == ""

    def test_empty_when_status_falsy(self):
        response = BuckarooResponse(make_response(text='{"Status": null}'))

        assert response.get_status_message() == ""


class TestGetPaymentKey:
    def test_returns_key_from_data(self):
        response = BuckarooResponse(make_response(text='{"Key": "abc-123"}'))

        assert response.get_payment_key() == "abc-123"

    def test_returns_none_when_key_missing(self):
        response = BuckarooResponse(make_response(text='{"Other": 1}'))

        assert response.get_payment_key() is None

    def test_returns_none_when_data_missing(self):
        response = BuckarooResponse(make_response(text=""))
        response._data = None

        assert response.get_payment_key() is None


class TestGetTransactionKey:
    def test_returns_key_from_services_list(self):
        body = '{"Services": [{"TransactionKey": "txn-1"}]}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_transaction_key() == "txn-1"

    def test_returns_key_from_services_dict_service_list(self):
        body = (
            '{"Services": {"ServiceList": [{"TransactionKey": "txn-dict"}]}}'
        )
        response = BuckarooResponse(make_response(text=body))

        assert response.get_transaction_key() == "txn-dict"

    def test_returns_none_when_services_missing(self):
        response = BuckarooResponse(make_response(text='{"Other": 1}'))

        assert response.get_transaction_key() is None

    def test_returns_none_when_services_list_empty(self):
        response = BuckarooResponse(make_response(text='{"Services": []}'))

        assert response.get_transaction_key() is None

    def test_returns_none_when_services_dict_service_list_empty(self):
        body = '{"Services": {"ServiceList": []}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_transaction_key() is None

    def test_returns_none_when_services_dict_has_no_service_list(self):
        body = '{"Services": {"Other": 1}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_transaction_key() is None

    def test_returns_none_when_data_missing(self):
        response = BuckarooResponse(make_response(text=""))
        response._data = None

        assert response.get_transaction_key() is None


class TestGetRedirectUrl:
    def test_returns_redirect_url_when_present(self):
        body = '{"RequiredAction": {"RedirectURL": "https://pay.example/redir"}}'
        response = BuckarooResponse(make_response(text=body))

        assert response.get_redirect_url() == "https://pay.example/redir"

    def test_returns_none_when_required_action_missing(self):
        response = BuckarooResponse(make_response(text='{"Other": 1}'))

        assert response.get_redirect_url() is None

    def test_returns_none_when_required_action_has_no_redirect_url(self):
        response = BuckarooResponse(
            make_response(text='{"RequiredAction": {"Other": 1}}')
        )

        assert response.get_redirect_url() is None

    def test_returns_none_when_data_missing(self):
        response = BuckarooResponse(make_response(text=""))
        response._data = None

        assert response.get_redirect_url() is None


class TestToDict:
    def test_includes_status_success_data_and_headers(self):
        headers = {"Content-Type": "application/json"}
        response = BuckarooResponse(
            make_response(
                status_code=201,
                text='{"Key": "k"}',
                headers=headers,
            )
        )

        assert response.to_dict() == {
            "status_code": 201,
            "success": True,
            "data": {"Key": "k"},
            "headers": headers,
        }
