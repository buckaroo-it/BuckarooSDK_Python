"""Tests for :class:`AuthorizeCaptureCapable`.

Exercises the capability mixin through a real :class:`BuckarooHttpClient`
wired to a recording :class:`MockBuckaroo`. Assertions read the request
shape off the recorded HTTP call (``json.loads(call["data"])``), never
builder internals.
"""

from __future__ import annotations

import json

import pytest

from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
    AuthorizeCaptureCapable,
)
from buckaroo.builders.payments.capabilities.encrypted_pay_capable import (
    EncryptedPayCapable,
)
from tests.support.builders import make_test_builder, populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import (
    recorded_action,
    recorded_request,
    wire_recording_http,
)


# ---------------------------------------------------------------------------
# Helpers


def _ready_builder(client, capabilities=(AuthorizeCaptureCapable,), allowed=None):
    """Build a fully-populated test builder so ``build()`` passes required checks."""
    builder = make_test_builder(
        client,
        service_name="dummy",
        allowed_params=allowed or {},
        capabilities=capabilities,
    )
    populate_required_fields(builder)
    return builder


# ---------------------------------------------------------------------------
# authorize()


class TestAuthorize:
    def test_authorize_posts_action_Authorize(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.authorize(validate=False)

        assert recorded_action(mock) == "Authorize"
        mock.assert_all_consumed()

    def test_authorize_posts_to_transaction_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        builder = _ready_builder(client)

        builder.authorize(validate=False)

        assert mock.calls[0]["method"] == "POST"
        assert "/json/transaction" in mock.calls[0]["url"].lower()


# ---------------------------------------------------------------------------
# authorizeEncrypted()


class TestAuthorizeEncrypted:
    def test_authorize_encrypted_posts_action_AuthorizeEncrypted(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.authorizeEncrypted(validate=False)

        assert recorded_action(mock) == "AuthorizeEncrypted"


# ---------------------------------------------------------------------------
# capture()
#
# AuthorizeCaptureCapable.capture is dead code: BaseBuilder.capture shadows
# it through the MRO on every real builder (see TestMroShadowing below). Any
# test calling the mixin method directly would only exercise unreachable code.
#
# ---------------------------------------------------------------------------
# cancelAuthorize()


class TestCancelAuthorize:
    @pytest.mark.parametrize(
        "key_source,expected_key",
        [
            ("arg", "key-from-arg"),
            ("original_transaction_key_payload", "key-from-otk"),
            ("authorization_key_payload", "key-from-auth"),
        ],
    )
    def test_cancel_authorize_reads_key_from_each_source(self, key_source, expected_key):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        if key_source == "arg":
            builder.cancelAuthorize(original_transaction_key=expected_key, validate=False)
        elif key_source == "original_transaction_key_payload":
            builder.from_dict({"original_transaction_key": expected_key})
            builder.cancelAuthorize(validate=False)
        else:
            builder.from_dict({"authorization_key": expected_key})
            builder.cancelAuthorize(validate=False)

        body = recorded_request(mock)
        assert body["OriginalTransactionKey"] == expected_key

    def test_cancel_authorize_arg_wins_over_payload(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        builder = _ready_builder(client)
        builder.from_dict(
            {
                "original_transaction_key": "from-payload",
                "authorization_key": "from-auth",
            }
        )

        builder.cancelAuthorize(original_transaction_key="from-arg", validate=False)

        assert recorded_request(mock)["OriginalTransactionKey"] == "from-arg"

    def test_cancel_authorize_without_any_key_raises_value_error(self):
        _, client = wire_recording_http()
        builder = _ready_builder(client)

        with pytest.raises(ValueError, match="original_transaction_key"):
            builder.cancelAuthorize(validate=False)

    def test_cancel_authorize_swaps_amount_debit_to_amount_credit(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        builder = _ready_builder(client)  # amount(10.0) sets _amount_debit

        builder.cancelAuthorize(original_transaction_key="abc", validate=False)

        body = recorded_request(mock)
        assert "AmountDebit" not in body
        assert body["AmountCredit"] == 10.0

    def test_cancel_authorize_posts_action_CancelAuthorize(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        builder = _ready_builder(client)

        builder.cancelAuthorize(original_transaction_key="abc", validate=False)

        assert recorded_action(mock) == "CancelAuthorize"

    def test_cancel_authorize_without_amount_debit_leaves_request_unswapped(self):
        """If the built request lacks AmountDebit, no swap happens."""
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        builder = _ready_builder(client)

        original_build = builder.build

        class _NoDebit:
            def __init__(self, underlying):
                self._underlying = underlying

            def to_dict(self):
                d = self._underlying.to_dict()
                d.pop("AmountDebit", None)
                return d

        def _build(action="Pay", validate=True, strict_validation=False):
            return _NoDebit(original_build(action, validate, strict_validation))

        builder.build = _build

        builder.cancelAuthorize(original_transaction_key="abc", validate=False)

        body = recorded_request(mock)
        assert "AmountDebit" not in body
        assert "AmountCredit" not in body

    def test_cancel_authorize_when_both_amounts_present_debit_replaces_credit(self):
        """When AmountDebit AND a pre-existing AmountCredit both appear on the
        built request, the swap clobbers AmountCredit with the old debit value.

        Implementation does ``req['AmountCredit'] = req.pop('AmountDebit')``,
        so any prior AmountCredit is lost. This pins that behavior.
        """
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        builder = _ready_builder(client)

        # Patch ``build`` so the resulting ``to_dict()`` returns a dict that
        # contains BOTH AmountCredit (5.0) AND AmountDebit (10.0) — a shape
        # the mixin has to resolve.
        original_build = builder.build

        class _BothAmounts:
            def __init__(self, underlying):
                self._underlying = underlying

            def to_dict(self):
                d = self._underlying.to_dict()
                d["AmountCredit"] = 5.0  # pre-existing credit
                return d

        def _build(action="Pay", validate=True, strict_validation=False):
            return _BothAmounts(original_build(action, validate, strict_validation))

        builder.build = _build

        builder.cancelAuthorize(original_transaction_key="abc", validate=False)

        body = recorded_request(mock)
        # AmountDebit gone; AmountCredit holds the former debit value (10.0).
        assert "AmountDebit" not in body
        assert body["AmountCredit"] == 10.0


# ---------------------------------------------------------------------------
# MRO / composition


class TestMroShadowing:
    """Pin how capability methods compose into a builder's MRO."""

    def test_base_builder_capture_shadows_mixin_capture(self):
        _, client = wire_recording_http()
        builder = _ready_builder(client)

        # The capture the instance resolves is BaseBuilder's (needs auth key).
        assert type(builder).capture.__qualname__ == "BaseBuilder.capture"
        # The mixin's simpler capture is still reachable via the class itself.
        assert AuthorizeCaptureCapable.capture.__qualname__ == (
            "AuthorizeCaptureCapable.capture"
        )

    def test_mixin_capture_posts_capture_action_when_invoked_directly(self):
        """Direct-invocation pin on the mixin's ``capture`` body.

        No composed builder routes to this method because ``BaseBuilder.capture``
        shadows it in MRO. The method is only callable as an unbound reference.
        Pinned here so the shadowed logic still has a behavioral contract.
        """
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "cap"}))
        builder = _ready_builder(client)

        response = AuthorizeCaptureCapable.capture(builder, validate=False)

        assert recorded_action(mock) == "Capture"
        assert response.key == "cap"


class TestMultiCapabilityBuilder:
    """Composing both mixins must expose all six action methods with no collisions."""

    def test_all_six_action_methods_invoke_and_post_expected_actions(self):
        """MRO-resolved action methods must each post the right Buckaroo Action.

        ``capture`` resolves to :meth:`BaseBuilder.capture` (needs an auth
        key) - the mixin's ``capture`` is dead code. This test pins both the
        resolution AND the on-wire Action for every method on a composed
        builder.
        """
        mock, client = wire_recording_http()
        # One queued response per invoked action (six total).
        for _ in range(6):
            mock.queue(
                BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"})
            )

        def _fresh_builder():
            b = make_test_builder(
                client,
                service_name="dummy",
                capabilities=(EncryptedPayCapable, AuthorizeCaptureCapable),
            )
            return populate_required_fields(b)

        calls = [
            ("pay", lambda b: b.pay(validate=False), "Pay"),
            ("authorize", lambda b: b.authorize(validate=False), "Authorize"),
            (
                "authorizeEncrypted",
                lambda b: b.authorizeEncrypted(validate=False),
                "AuthorizeEncrypted",
            ),
            (
                "capture",
                lambda b: b.capture(original_transaction_key="AUTH-1", validate=False),
                "Capture",
            ),
            (
                "payEncrypted",
                lambda b: b.payEncrypted(validate=False),
                "PayEncrypted",
            ),
            (
                "cancelAuthorize",
                lambda b: b.cancelAuthorize(
                    original_transaction_key="AUTH-1", validate=False
                ),
                "CancelAuthorize",
            ),
        ]

        for _name, invoke, _action in calls:
            invoke(_fresh_builder())

        observed = [
            json.loads(c["data"])["Services"]["ServiceList"][0]["Action"]
            for c in mock.calls
        ]
        expected = [action for _, _, action in calls]
        assert observed == expected

    def test_authorize_and_payEncrypted_coexist(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))

        builder = make_test_builder(
            client,
            service_name="dummy",
            capabilities=(EncryptedPayCapable, AuthorizeCaptureCapable),
        )
        builder.currency("EUR").amount(10.0).description("d").invoice("I").return_url(
            "https://e/ok"
        ).return_url_cancel("https://e/c").return_url_error("https://e/e").return_url_reject(
            "https://e/r"
        )

        builder.authorize(validate=False)
        builder.payEncrypted(validate=False)

        actions = [
            json.loads(c["data"])["Services"]["ServiceList"][0]["Action"]
            for c in mock.calls
        ]
        assert actions == ["Authorize", "PayEncrypted"]
