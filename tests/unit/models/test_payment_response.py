"""Tests for buckaroo.models.payment_response."""

import pytest

from buckaroo.models.payment_response import (
    BuckarooStatusCode,
    PaymentResponse,
    RequiredAction,
    Service,
    ServiceParameter,
    Status,
    StatusCode,
)


PENDING_CODES = (
    BuckarooStatusCode.PENDING_INPUT,
    BuckarooStatusCode.PENDING_PROCESSING,
    BuckarooStatusCode.AWAITING_CONSUMER,
    BuckarooStatusCode.ON_HOLD,
)
CANCELLED_CODES = (
    BuckarooStatusCode.CANCELLED_BY_CONSUMER,
    BuckarooStatusCode.CANCELLED_BY_MERCHANT,
)
FAILED_CODES = (
    BuckarooStatusCode.PAYMENT_FAILED,
    BuckarooStatusCode.VALIDATION_FAILED,
    BuckarooStatusCode.TECHNICAL_ERROR,
    BuckarooStatusCode.REJECTED,
)


# --- StatusCode.from_dict ---


def test_status_code_from_full_dict():
    sc = StatusCode.from_dict({"Code": 190, "Description": "Success"})
    assert sc.code == 190
    assert sc.description == "Success"


def test_status_code_from_partial_dict_missing_description():
    sc = StatusCode.from_dict({"Code": 490})
    assert sc.code == 490
    assert sc.description == ""


def test_status_code_from_empty_dict():
    sc = StatusCode.from_dict({})
    assert sc.code == 0
    assert sc.description == ""


def test_status_code_from_none():
    sc = StatusCode.from_dict(None)
    assert sc.code == 0
    assert sc.description == ""


def test_status_code_from_integer():
    sc = StatusCode.from_dict(490)
    assert sc.code == 490
    assert sc.description == ""


def test_status_code_from_unexpected_type():
    sc = StatusCode.from_dict("nope")
    assert sc.code == 0
    assert sc.description == ""


# --- Status.from_dict ---


def test_status_from_full_dict():
    status = Status.from_dict(
        {
            "Code": {"Code": 190, "Description": "Success"},
            "SubCode": {"Code": 1, "Description": "Sub"},
            "DateTime": "2024-01-01T00:00:00",
        }
    )
    assert status.code.code == 190
    assert status.sub_code.code == 1
    assert status.datetime == "2024-01-01T00:00:00"


def test_status_from_dict_with_null_sub_code():
    status = Status.from_dict(
        {
            "Code": {"Code": 190, "Description": "Success"},
            "SubCode": None,
        }
    )
    assert status.code.code == 190
    assert status.sub_code.code == 0
    assert status.datetime == ""


def test_status_from_empty_dict():
    status = Status.from_dict({})
    assert status.code.code == 0
    assert status.sub_code.code == 0
    assert status.datetime == ""


def test_status_from_none():
    status = Status.from_dict(None)
    assert status.code.code == 0


# --- RequiredAction.from_dict ---


def test_required_action_from_full_dict():
    ra = RequiredAction.from_dict(
        {
            "RedirectURL": "https://example.com/pay",
            "RequestedInformation": {"field": "foo"},
            "PayRemainderDetails": {"remainder": 10},
            "Name": "Redirect",
            "TypeDeprecated": 1,
        }
    )
    assert ra.redirect_url == "https://example.com/pay"
    assert ra.requested_information == {"field": "foo"}
    assert ra.pay_remainder_details == {"remainder": 10}
    assert ra.name == "Redirect"
    assert ra.type_deprecated == 1


def test_required_action_from_empty_dict():
    ra = RequiredAction.from_dict({})
    assert ra.redirect_url is None
    assert ra.requested_information is None
    assert ra.pay_remainder_details is None
    assert ra.name == ""
    assert ra.type_deprecated == 0


def test_required_action_from_none():
    ra = RequiredAction.from_dict(None)
    assert ra.redirect_url is None
    assert ra.name == ""


# --- ServiceParameter.from_dict ---


def test_service_parameter_from_full_dict():
    sp = ServiceParameter.from_dict({"Name": "TransactionId", "Value": "abc"})
    assert sp.name == "TransactionId"
    assert sp.value == "abc"


def test_service_parameter_from_empty_dict():
    sp = ServiceParameter.from_dict({})
    assert sp.name == ""
    assert sp.value is None


def test_service_parameter_from_none():
    sp = ServiceParameter.from_dict(None)
    assert sp.name == ""
    assert sp.value is None


# --- Service.from_dict ---


def test_service_from_full_dict():
    svc = Service.from_dict(
        {
            "Name": "ideal",
            "Action": "Pay",
            "Parameters": [
                {"Name": "TransactionId", "Value": "tx1"},
                {"Name": "IssuerId", "Value": "ABNANL2A"},
            ],
        }
    )
    assert svc.name == "ideal"
    assert svc.action == "Pay"
    assert len(svc.parameters) == 2
    assert svc.parameters[0].name == "TransactionId"
    assert svc.parameters[0].value == "tx1"


def test_service_from_dict_without_parameters():
    svc = Service.from_dict({"Name": "ideal"})
    assert svc.name == "ideal"
    assert svc.action is None
    assert svc.parameters == []


def test_service_from_dict_with_empty_parameters_list():
    svc = Service.from_dict({"Name": "ideal", "Parameters": []})
    assert svc.parameters == []


def test_service_from_empty_dict():
    svc = Service.from_dict({})
    assert svc.name == ""
    assert svc.parameters == []


def test_service_from_none():
    svc = Service.from_dict(None)
    assert svc.name == ""
    assert svc.parameters == []


# --- PaymentResponse basic construction ---


def test_payment_response_from_empty_dict_does_not_raise():
    resp = PaymentResponse({})
    assert resp.status is None
    assert resp.required_action is None
    assert resp.services == []
    assert resp.is_pending() is False
    assert resp.is_successful() is False
    assert resp.is_cancelled() is False
    assert resp.is_failed() is False
    assert resp.requires_action() is False
    assert resp.get_redirect_url() is None
    assert resp.get_transaction_id() is None
    assert resp.get_service_parameter("anything") is None


def test_payment_response_from_none():
    resp = PaymentResponse(None)
    assert resp.to_dict() == {}
    assert resp.status is None


def test_payment_response_is_successful_uses_raw_flag():
    resp = PaymentResponse({"is_successful_payment": True})
    assert resp.is_successful() is True


def test_payment_response_parses_basic_fields():
    resp = PaymentResponse(
        {
            "status_code": 200,
            "success": True,
            "headers": {"X-Test": "1"},
            "transaction_key": "txkey",
            "buckaroo_status_code": 190,
            "buckaroo_status_message": "Success",
            "redirect_url": "https://legacy.example/",
            "data": {
                "Key": "KEY1",
                "PaymentKey": "PK1",
                "Invoice": "INV-1",
                "ServiceCode": "ideal",
                "IsTest": True,
                "Currency": "EUR",
                "AmountDebit": 12.50,
                "AmountCredit": 0,
                "TransactionType": "C021",
                "MutationType": 1,
                "CustomParameters": {"a": 1},
                "AdditionalParameters": {"b": 2},
                "RequestErrors": None,
                "RelatedTransactions": [],
                "ConsumerMessage": "Thanks",
                "Order": "ORD-1",
                "IssuingCountry": "NL",
                "StartRecurrent": True,
                "Recurring": True,
                "CustomerName": "Jane",
                "PayerHash": "hash",
            },
        }
    )
    assert resp.status_code == 200
    assert resp.success is True
    assert resp.headers == {"X-Test": "1"}
    assert resp.key == "KEY1"
    assert resp.payment_key == "PK1"
    assert resp.invoice == "INV-1"
    assert resp.service_code == "ideal"
    assert resp.is_test is True
    assert resp.currency == "EUR"
    assert resp.amount_debit == 12.50
    assert resp.amount_credit == 0
    assert resp.transaction_type == "C021"
    assert resp.mutation_type == 1
    assert resp.custom_parameters == {"a": 1}
    assert resp.additional_parameters == {"b": 2}
    assert resp.request_errors is None
    assert resp.related_transactions == []
    assert resp.consumer_message == "Thanks"
    assert resp.order == "ORD-1"
    assert resp.issuing_country == "NL"
    assert resp.start_recurrent is True
    assert resp.recurring is True
    assert resp.customer_name == "Jane"
    assert resp.payer_hash == "hash"
    assert resp.transaction_key == "txkey"
    assert resp.buckaroo_status_code == 190
    assert resp.buckaroo_status_message == "Success"
    assert resp.redirect_url == "https://legacy.example/"
    assert resp.to_dict()["status_code"] == 200


# --- Status predicates parametrised over enum ---


@pytest.mark.parametrize("code", PENDING_CODES)
def test_is_pending_true_for_pending_codes(code):
    resp = _response_with_status_code(code)
    assert resp.is_pending() is True
    assert resp.is_cancelled() is False
    assert resp.is_failed() is False


@pytest.mark.parametrize("code", CANCELLED_CODES)
def test_is_cancelled_true_for_cancelled_codes(code):
    resp = _response_with_status_code(code)
    assert resp.is_cancelled() is True
    assert resp.is_pending() is False
    assert resp.is_failed() is False


@pytest.mark.parametrize("code", FAILED_CODES)
def test_is_failed_true_for_failed_codes(code):
    resp = _response_with_status_code(code)
    assert resp.is_failed() is True
    assert resp.is_pending() is False
    assert resp.is_cancelled() is False


def test_success_code_matches_no_predicate():
    resp = _response_with_status_code(BuckarooStatusCode.SUCCESS)
    assert resp.is_pending() is False
    assert resp.is_cancelled() is False
    assert resp.is_failed() is False


def test_is_successful_with_190_status_and_success_flag():
    resp = PaymentResponse(
        {
            "is_successful_payment": True,
            "data": {
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
            },
        }
    )
    assert resp.is_successful() is True
    assert resp.is_pending() is False
    assert resp.is_cancelled() is False
    assert resp.is_failed() is False


def test_predicates_false_when_no_status():
    resp = PaymentResponse({})
    assert resp.is_pending() is False
    assert resp.is_cancelled() is False
    assert resp.is_failed() is False


# --- get_redirect_url ---


def test_get_redirect_url_none_without_required_action():
    resp = PaymentResponse({"data": {}})
    assert resp.get_redirect_url() is None


def test_get_redirect_url_returns_required_action_url():
    resp = PaymentResponse(
        {
            "data": {
                "RequiredAction": {
                    "RedirectURL": "https://checkout.example/pay/1",
                    "Name": "Redirect",
                }
            }
        }
    )
    assert resp.requires_action() is True
    assert resp.get_redirect_url() == "https://checkout.example/pay/1"


# --- get_transaction_id / get_service_parameter ---


def test_get_transaction_id_returns_value_when_present():
    resp = PaymentResponse(
        {
            "data": {
                "Services": [
                    {
                        "Name": "ideal",
                        "Parameters": [
                            {"Name": "TransactionId", "Value": "TX-123"},
                        ],
                    }
                ]
            }
        }
    )
    assert resp.get_transaction_id() == "TX-123"


def test_get_transaction_id_none_when_missing():
    resp = PaymentResponse(
        {"data": {"Services": [{"Name": "ideal", "Parameters": [{"Name": "Other", "Value": "x"}]}]}}
    )
    assert resp.get_transaction_id() is None


def test_get_service_parameter_case_insensitive():
    resp = PaymentResponse(
        {
            "data": {
                "Services": [
                    {
                        "Name": "ideal",
                        "Parameters": [
                            {"Name": "ConsumerIBAN", "Value": "NL00RABO0123456789"},
                        ],
                    }
                ]
            }
        }
    )
    assert resp.get_service_parameter("consumeriban") == "NL00RABO0123456789"


def test_get_service_parameter_returns_none_for_missing_key():
    resp = PaymentResponse(
        {"data": {"Services": [{"Name": "ideal", "Parameters": [{"Name": "A", "Value": 1}]}]}}
    )
    assert resp.get_service_parameter("NotThere") is None


# --- __str__ / __repr__ ---


def test_str_includes_status_and_amount():
    resp = PaymentResponse(
        {
            "data": {
                "Key": "K",
                "Currency": "EUR",
                "AmountDebit": 9.99,
                "Status": {
                    "Code": {"Code": int(BuckarooStatusCode.SUCCESS), "Description": "Success"}
                },
            }
        }
    )
    s = str(resp)
    assert "PaymentResponse(" in s
    assert "key=K" in s
    assert f"{int(BuckarooStatusCode.SUCCESS)} - Success" in s
    assert "9.99 EUR" in s


def test_str_with_unknown_status():
    resp = PaymentResponse({"data": {"Key": "K"}})
    assert "status=Unknown" in str(resp)


def test_repr_includes_all_fields():
    resp = PaymentResponse(
        {
            "status_code": 200,
            "success": True,
            "data": {
                "Key": "K",
                "PaymentKey": "PK",
                "IsTest": False,
                "Currency": "EUR",
                "AmountDebit": 1.0,
            },
        }
    )
    r = repr(resp)
    assert "key=K" in r
    assert "payment_key=PK" in r
    assert "status_code=200" in r
    assert "success=True" in r
    assert "is_test=False" in r
    assert "currency=EUR" in r
    assert "amount=1.0" in r


# --- Helpers ---


def _response_with_status_code(code: int) -> PaymentResponse:
    return PaymentResponse(
        {
            "data": {
                "Status": {"Code": {"Code": int(code), "Description": ""}},
            }
        }
    )


def test_get_some_error_returns_first_request_error_with_priority():
    """RequestErrors take precedence over ConsumerMessage/Message/SubCode."""
    response = PaymentResponse(
        {
            "data": {
                "RequestErrors": {
                    "ChannelErrors": [{"ErrorMessage": "Channel boom"}],
                    "ServiceErrors": [{"ErrorMessage": "Service boom"}],
                },
                "ConsumerMessage": {"HtmlText": "Consumer boom"},
                "Message": "Top-level boom",
                "Status": {
                    "SubCode": {"Code": "S", "Description": "Sub boom"},
                },
            }
        }
    )
    assert response.has_some_error() is True
    assert response.get_some_error() == "Channel boom"


def test_get_some_error_walks_request_error_buckets_in_order():
    """When ChannelErrors empty, fall through to ServiceErrors etc."""
    response = PaymentResponse(
        {
            "data": {
                "RequestErrors": {
                    "ChannelErrors": [],
                    "ServiceErrors": [{"ErrorMessage": "Service boom"}],
                    "ParameterErrors": [{"ErrorMessage": "Param boom"}],
                }
            }
        }
    )
    assert response.get_some_error() == "Service boom"


def test_get_some_error_falls_back_to_consumer_message():
    response = PaymentResponse(
        {
            "data": {
                "ConsumerMessage": {"HtmlText": "Card declined"},
                "Message": "Top-level boom",
            }
        }
    )
    assert response.get_some_error() == "Card declined"


def test_get_some_error_falls_back_to_top_level_message():
    response = PaymentResponse({"data": {"Message": "Gateway down"}})
    assert response.get_some_error() == "Gateway down"


def test_get_some_error_falls_back_to_sub_code_description():
    """Riverty 491 stuffs the ``Authorize rejected. ...`` text here."""
    riverty_msg = "Authorize rejected. The following errors occurred: File format is not supported."
    response = PaymentResponse(
        {
            "data": {
                "Status": {
                    "Code": {"Code": 491, "Description": "Validation failure"},
                    "SubCode": {"Code": "S001", "Description": riverty_msg},
                }
            }
        }
    )
    assert response.get_some_error() == riverty_msg


def test_get_some_error_returns_empty_when_no_source():
    response = PaymentResponse({"data": {}})
    assert response.has_some_error() is False
    assert response.get_some_error() == ""


def test_has_error_ignores_empty_buckets():
    response = PaymentResponse(
        {"data": {"RequestErrors": {"ChannelErrors": [], "ServiceErrors": []}}}
    )
    assert response.has_error() is False
    assert response.get_first_error() == {}


def test_has_consumer_message_handles_missing_html_text():
    response = PaymentResponse({"data": {"ConsumerMessage": {}}})
    assert response.has_consumer_message() is False
    assert response.get_consumer_message() == ""


def test_has_sub_code_message_false_when_description_blank():
    response = PaymentResponse({"data": {"Status": {"SubCode": {"Code": "X", "Description": ""}}}})
    assert response.has_sub_code_message() is False
    assert response.get_sub_code_message() == ""


# --- RequestErrors defensive parsing ---


def test_has_error_handles_dict_bucket():
    """RequestErrors bucket is a single dict (not a list)."""
    response = PaymentResponse(
        {
            "data": {
                "RequestErrors": {
                    "ChannelErrors": {"ErrorMessage": "Single bucket boom"},
                }
            }
        }
    )
    assert response.has_error() is True
    assert response.get_first_error() == {"ErrorMessage": "Single bucket boom"}
    assert response.get_some_error() == "Single bucket boom"


def test_has_error_skips_non_list_non_dict_bucket():
    """Bucket value that is neither list nor dict is ignored."""
    response = PaymentResponse(
        {
            "data": {
                "RequestErrors": {
                    "ChannelErrors": "not a real shape",
                    "ServiceErrors": [{"ErrorMessage": "Service boom"}],
                }
            }
        }
    )
    assert response.has_error() is True
    assert response.get_some_error() == "Service boom"


def test_get_some_error_skips_entries_missing_error_message():
    """Entries without ``ErrorMessage`` fall through to the next entry."""
    response = PaymentResponse(
        {
            "data": {
                "RequestErrors": {
                    "ChannelErrors": [
                        {"Name": "no message here"},
                        {"ErrorMessage": "Found it"},
                    ]
                }
            }
        }
    )
    assert response.get_some_error() == "Found it"


def test_get_some_error_skips_blank_error_message():
    """Blank ``ErrorMessage`` falls through to the next non-blank entry,
    even across buckets."""
    response = PaymentResponse(
        {
            "data": {
                "RequestErrors": {
                    "ChannelErrors": [{"ErrorMessage": ""}],
                    "ServiceErrors": [{"ErrorMessage": "Real one"}],
                }
            }
        }
    )
    assert response.get_some_error() == "Real one"


def test_has_error_false_when_request_errors_is_scalar():
    """Non-dict RequestErrors (e.g. unexpected scalar) is treated as empty."""
    response = PaymentResponse({"data": {"RequestErrors": "boom"}})
    assert response.has_error() is False
    assert response.get_first_error() == {}
    assert response.get_some_error() == ""
