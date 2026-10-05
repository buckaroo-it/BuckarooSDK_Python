"""Low-level payment verdicts and existing high-level response contracts."""

import json

import pytest

from buckaroo.http.client import BuckarooResponse
from buckaroo.http.strategies import HttpResponse


@pytest.mark.parametrize(
    "status,expected",
    [
        ({"Code": code}, code == 190)
        for code in [190, 490, 491, 492, 690, 790, 791, 792, 793, 794, 890, 891, 999]
    ]
    + [({"Code": {"Code": code}}, code == 190) for code in [190, 490, 791]]
    + [
        (status, False)
        for status in [
            None,
            {},
            [],
            "invalid",
            190,
            {"Code": None},
            {"Code": []},
            {"Code": "190"},
            {"Code": 190.0},
        ]
    ],
)
def test_payment_success_requires_explicit_paid_status(status, expected):
    data = {"Status": status, "RequiredAction": {"RedirectURL": "https://example.invalid/pay"}}
    raw = HttpResponse(200, {}, json.dumps(data), True)
    assert BuckarooResponse(raw).is_successful_payment() is expected


@pytest.mark.parametrize("body", ["", "{}", "null", "[]", '"invalid"'])
def test_missing_payment_status_is_not_paid(body):
    assert BuckarooResponse(HttpResponse(200, {}, body, True)).is_successful_payment() is False


def test_http_failure_is_not_payment_success():
    from buckaroo.models.payment_response import PaymentResponse

    raw = HttpResponse(500, {}, '{"Status":{"Code":190}}', False)
    response = BuckarooResponse(raw)
    assert response.is_successful_payment() is False
    assert PaymentResponse(response.to_dict()).is_successful() is False


@pytest.mark.parametrize("flag", [True, False])
def test_high_level_response_preserves_explicit_success_flag(flag):
    from buckaroo.models.payment_response import PaymentResponse

    # The high-level wrapper accepts a caller-supplied verdict independently
    # of the transport response; keep that existing contract.
    for envelope in [{}, {"status_code": 200, "success": True, "data": {"Status": {"Code": 190}}}]:
        response = PaymentResponse({**envelope, "is_successful_payment": flag})
        assert response.is_successful() is flag
