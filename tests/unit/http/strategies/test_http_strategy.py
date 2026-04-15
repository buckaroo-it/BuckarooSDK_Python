"""Unit tests for buckaroo.http.strategies.http_strategy."""

import pytest

from buckaroo.http.strategies.http_strategy import HttpResponse, HttpStrategy


class TestHttpResponseFields:
    def test_stores_constructor_values(self):
        response = HttpResponse(
            status_code=201,
            headers={"Content-Type": "application/json"},
            text='{"ok": true}',
            success=True,
        )

        assert response.status_code == 201
        assert response.headers == {"Content-Type": "application/json"}
        assert response.text == '{"ok": true}'
        assert response.success is True

    def test_success_flag_honors_caller_input_even_when_status_suggests_failure(self):
        response = HttpResponse(
            status_code=500,
            headers={},
            text="",
            success=True,
        )

        assert response.success is True

    def test_success_flag_honors_caller_input_even_when_status_suggests_success(self):
        response = HttpResponse(
            status_code=200,
            headers={},
            text="",
            success=False,
        )

        assert response.success is False


class TestHttpResponseJson:
    def test_parses_valid_json_text(self):
        response = HttpResponse(
            status_code=200,
            headers={},
            text='{"key": "value", "n": 7}',
            success=True,
        )

        assert response.json() == {"key": "value", "n": 7}

    def test_empty_text_returns_empty_dict(self):
        response = HttpResponse(
            status_code=204,
            headers={},
            text="",
            success=True,
        )

        assert response.json() == {}

    def test_invalid_json_returns_raw_content(self):
        response = HttpResponse(
            status_code=200,
            headers={},
            text="<html>not json</html>",
            success=False,
        )

        assert response.json() == {"raw_content": "<html>not json</html>"}


class TestHttpStrategyAbstract:
    def test_direct_instantiation_raises_type_error(self):
        with pytest.raises(TypeError):
            HttpStrategy()

    @pytest.mark.parametrize(
        "method_name",
        ["configure", "request", "is_available", "get_name"],
    )
    def test_method_is_abstract(self, method_name):
        method = HttpStrategy.__dict__[method_name]
        assert getattr(method, "__isabstractmethod__", False) is True

    def test_abstract_method_set_is_exactly_the_four_declared(self):
        assert HttpStrategy.__abstractmethods__ == frozenset(
            {"configure", "request", "is_available", "get_name"}
        )

    def test_subclass_missing_any_method_cannot_instantiate(self):
        class PartialStrategy(HttpStrategy):
            def configure(self, **kwargs):
                pass

            def is_available(self):
                return True

            def get_name(self):
                return "partial"

        with pytest.raises(TypeError):
            PartialStrategy()

    def test_concrete_subclass_implementing_all_four_methods_instantiates(self):
        class FakeStrategy(HttpStrategy):
            def __init__(self):
                self.configured_with = None

            def configure(self, **kwargs):
                self.configured_with = kwargs

            def request(
                self,
                method,
                url,
                headers=None,
                data=None,
                timeout=None,
                verify_ssl=True,
            ):
                return HttpResponse(
                    status_code=200,
                    headers={},
                    text="{}",
                    success=True,
                )

            def is_available(self):
                return True

            def get_name(self):
                return "fake"

        strategy = FakeStrategy()

        strategy.configure(timeout=5)
        response = strategy.request("GET", "https://example.test")

        assert isinstance(strategy, HttpStrategy)
        assert strategy.configured_with == {"timeout": 5}
        assert strategy.is_available() is True
        assert strategy.get_name() == "fake"
        assert response.status_code == 200


