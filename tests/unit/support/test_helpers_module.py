"""Unit tests for tests.support.helpers.Helpers."""

from __future__ import annotations

import re

from tests.support.helpers import Helpers


class TestGenerateTransactionKey:
    def test_returns_32_char_uppercase_hex(self) -> None:
        key = Helpers.generate_transaction_key()

        assert len(key) == 32
        assert re.fullmatch(r"[0-9A-F]{32}", key) is not None

    def test_returns_unique_values(self) -> None:
        assert Helpers.generate_transaction_key() != Helpers.generate_transaction_key()


class TestSuccessResponse:
    def test_status_code_is_190(self) -> None:
        response = Helpers.success_response()

        assert response["Status"]["Code"]["Code"] == 190
        assert response["Status"]["Code"]["Description"] == "Success"

    def test_includes_buckaroo_shaped_defaults(self) -> None:
        response = Helpers.success_response()

        assert response["Status"]["SubCode"] == {
            "Code": "S001",
            "Description": "Transaction successful",
        }
        assert response["RequiredAction"] is None
        assert response["Services"] == []
        assert response["ServiceCode"] == "creditcard"
        assert response["IsTest"] is True
        assert response["Currency"] == "EUR"
        assert response["AmountDebit"] == 10.00
        assert response["Invoice"].startswith("INV-")
        assert re.fullmatch(r"[0-9A-F]{32}", response["Key"]) is not None
        # ISO-8601 datetime, second precision
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", response["Status"]["DateTime"])

    def test_overrides_shallow_merge_top_level(self) -> None:
        response = Helpers.success_response(overrides={"Key": "X"})

        assert response["Key"] == "X"
        # The rest of the dict is untouched.
        assert response["Status"]["Code"]["Code"] == 190
        assert response["Currency"] == "EUR"

    def test_overrides_defaults_to_none(self) -> None:
        # Passing None (the default) must behave like no overrides.
        response = Helpers.success_response(overrides=None)

        assert response["Status"]["Code"]["Code"] == 190


class TestFailedResponse:
    def test_status_code_is_490(self) -> None:
        response = Helpers.failed_response()

        assert response["Status"]["Code"]["Code"] == 490
        assert response["Status"]["Code"]["Description"] == "Failed"

    def test_default_error_message(self) -> None:
        response = Helpers.failed_response()

        assert response["Status"]["SubCode"] == {
            "Code": "F001",
            "Description": "Transaction failed",
        }

    def test_custom_error_in_subcode_description(self) -> None:
        response = Helpers.failed_response("oops")

        assert response["Status"]["SubCode"]["Description"] == "oops"
        assert response["Status"]["SubCode"]["Code"] == "F001"

    def test_inherits_success_response_shape(self) -> None:
        response = Helpers.failed_response("boom")

        # Non-Status fields come from success_response.
        assert response["ServiceCode"] == "creditcard"
        assert response["Currency"] == "EUR"
        assert response["AmountDebit"] == 10.00
        assert response["IsTest"] is True

    def test_overrides_respected(self) -> None:
        response = Helpers.failed_response("x", overrides={"Currency": "USD"})

        assert response["Currency"] == "USD"
        assert response["Status"]["Code"]["Code"] == 490
        assert response["Status"]["SubCode"]["Description"] == "x"

    def test_overrides_defaults_to_none(self) -> None:
        response = Helpers.failed_response("x", overrides=None)

        assert response["Status"]["Code"]["Code"] == 490
        assert response["Currency"] == "EUR"
