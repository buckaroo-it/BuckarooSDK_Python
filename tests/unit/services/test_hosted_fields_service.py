"""Tests for :class:`buckaroo.services.hosted_fields_service.HostedFieldsService`."""

from __future__ import annotations

import base64

import pytest

from buckaroo.exceptions._buckaroo_error import BuckarooError
from buckaroo.services.hosted_fields_service import HostedFieldsService
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import RecordingMock


def _make_service(mock: RecordingMock, **kwargs) -> HostedFieldsService:
    return HostedFieldsService(
        client_id=kwargs.pop("client_id", "cid"),
        client_secret=kwargs.pop("client_secret", "csec"),
        http_strategy=mock,
        **kwargs,
    )


class TestGetToken:
    def test_returns_parsed_json_response(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST",
                HostedFieldsService.OAUTH_TOKEN_URL,
                {"access_token": "tok-123", "expires_in": 3600, "token_type": "Bearer"},
            )
        )
        svc = _make_service(mock_strategy)

        token = svc.get_token()

        assert token["access_token"] == "tok-123"
        assert token["expires_in"] == 3600

    def test_uses_default_scope_when_not_provided(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST",
                HostedFieldsService.OAUTH_TOKEN_URL,
                {"access_token": "x"},
            )
        )
        svc = _make_service(mock_strategy)

        svc.get_token()

        assert "scope=hostedfields%3Asave" in mock_strategy.calls[0]["data"]

    def test_overrides_scope_when_explicit(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST",
                HostedFieldsService.OAUTH_TOKEN_URL,
                {"access_token": "x"},
            )
        )
        svc = _make_service(mock_strategy)

        svc.get_token("custom:scope")

        assert "scope=custom%3Ascope" in mock_strategy.calls[0]["data"]

    def test_sends_basic_auth_header(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", HostedFieldsService.OAUTH_TOKEN_URL, {"access_token": "x"}
            )
        )
        svc = _make_service(mock_strategy, client_id="abc", client_secret="def")

        svc.get_token()

        expected_creds = base64.b64encode(b"abc:def").decode()
        assert mock_strategy.calls[0]["headers"]["Authorization"] == f"Basic {expected_creds}"

    def test_sends_form_encoded_body_with_grant_type(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", HostedFieldsService.OAUTH_TOKEN_URL, {"access_token": "x"}
            )
        )
        svc = _make_service(mock_strategy)

        svc.get_token()

        call = mock_strategy.calls[0]
        assert call["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
        assert "grant_type=client_credentials" in call["data"]

    def test_posts_to_oauth_endpoint(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", HostedFieldsService.OAUTH_TOKEN_URL, {"access_token": "x"}
            )
        )
        svc = _make_service(mock_strategy)

        svc.get_token()

        assert mock_strategy.calls[0]["method"] == "POST"
        assert mock_strategy.calls[0]["url"] == HostedFieldsService.OAUTH_TOKEN_URL

    def test_raises_on_http_error_with_parsed_error_code(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST",
                HostedFieldsService.OAUTH_TOKEN_URL,
                {"error": "invalid_client", "error_description": "bad creds"},
                status=401,
            )
        )
        svc = _make_service(mock_strategy)

        with pytest.raises(BuckarooError) as exc_info:
            svc.get_token()

        msg = str(exc_info.value)
        assert "invalid_client" in msg
        assert "bad creds" in msg

    def test_raises_on_network_error(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest(
                "POST", HostedFieldsService.OAUTH_TOKEN_URL
            ).with_exception(Exception("connection refused"))
        )
        svc = _make_service(mock_strategy)

        with pytest.raises(BuckarooError) as exc_info:
            svc.get_token()
        assert "connection refused" in str(exc_info.value)

    def test_raises_on_empty_body(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.text(
                "POST",
                HostedFieldsService.OAUTH_TOKEN_URL,
                "",
                content_type="application/json",
            )
        )
        svc = _make_service(mock_strategy)

        with pytest.raises(BuckarooError):
            svc.get_token()

    def test_raises_on_malformed_json(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.text(
                "POST",
                HostedFieldsService.OAUTH_TOKEN_URL,
                "not-json",
                content_type="application/json",
            )
        )
        svc = _make_service(mock_strategy)

        with pytest.raises(BuckarooError):
            svc.get_token()

    def test_passes_configured_timeout(self, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", HostedFieldsService.OAUTH_TOKEN_URL, {"access_token": "x"}
            )
        )
        svc = _make_service(mock_strategy, timeout=42)

        svc.get_token()

        assert mock_strategy.calls[0]["timeout"] == 42


class TestConstruction:
    def test_rejects_empty_client_id(self, mock_strategy):
        with pytest.raises(ValueError):
            HostedFieldsService(client_id="", client_secret="x", http_strategy=mock_strategy)

    def test_rejects_empty_client_secret(self, mock_strategy):
        with pytest.raises(ValueError):
            HostedFieldsService(client_id="x", client_secret="", http_strategy=mock_strategy)
