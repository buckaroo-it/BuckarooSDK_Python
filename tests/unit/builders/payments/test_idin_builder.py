"""Unit coverage for :class:`IdinBuilder`.

iDIN drives three DataRequest actions — ``identify`` (full identification),
``verify`` (age verification), and ``login`` (unique consumer ID) — each
carrying a single ``issuerId`` (BIC code of the consumer's bank) service
parameter. Bank personal data arrives later via push; the immediate response
only carries the redirect, so no custom response model is needed.
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.idin_builder import IdinBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.factories.payment_method_factory import PaymentMethodFactory


def test_builder_instantiates_as_payment_builder(client: BuckarooClient) -> None:
    builder = IdinBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_idin(client: BuckarooClient) -> None:
    assert IdinBuilder(client).get_service_name() == "Idin"


_ISSUER_ID_SPEC = {
    "issuerId": {
        "type": str,
        "required": True,
        "description": "BIC code of the issuing bank of the consumer",
    },
}


def test_get_allowed_service_parameters_identify_requires_issuer_id(
    client: BuckarooClient,
) -> None:
    assert IdinBuilder(client).get_allowed_service_parameters("identify") == _ISSUER_ID_SPEC


def test_get_allowed_service_parameters_verify_requires_issuer_id(
    client: BuckarooClient,
) -> None:
    assert IdinBuilder(client).get_allowed_service_parameters("verify") == _ISSUER_ID_SPEC


def test_get_allowed_service_parameters_login_requires_issuer_id(
    client: BuckarooClient,
) -> None:
    assert IdinBuilder(client).get_allowed_service_parameters("login") == _ISSUER_ID_SPEC


def test_get_allowed_service_parameters_is_case_insensitive(client: BuckarooClient) -> None:
    builder = IdinBuilder(client)
    assert builder.get_allowed_service_parameters(
        "Identify"
    ) == builder.get_allowed_service_parameters("identify")


def test_get_allowed_service_parameters_unknown_action_returns_empty(
    client: BuckarooClient,
) -> None:
    assert IdinBuilder(client).get_allowed_service_parameters("Pay") == {}


def test_required_fields_only_return_url_family(client: BuckarooClient) -> None:
    builder = (
        IdinBuilder(client)
        .return_url("https://example.com/return")
        .return_url_cancel("https://example.com/cancel")
        .return_url_error("https://example.com/error")
        .return_url_reject("https://example.com/reject")
    )
    assert builder.required_fields("identify") == {
        "return_url": "https://example.com/return",
        "return_url_cancel": "https://example.com/cancel",
        "return_url_error": "https://example.com/error",
        "return_url_reject": "https://example.com/reject",
    }


def test_create_builder_returns_idin_builder(client: BuckarooClient) -> None:
    builder = PaymentMethodFactory.create_builder("idin", client)
    assert isinstance(builder, IdinBuilder)
