"""Tests for buckaroo.models.payment_request DTOs."""

from buckaroo.models.payment_request import (
    ClientIP,
    Parameter,
    PaymentRequest,
    Service,
    ServiceList,
)


def _make_request(**overrides):
    defaults = dict(
        currency="EUR",
        amount_debit=10.50,
        description="Order 42",
        invoice="INV-42",
        return_url="https://example.com/return",
        return_url_cancel="https://example.com/cancel",
        return_url_error="https://example.com/error",
        return_url_reject="https://example.com/reject",
    )
    defaults.update(overrides)
    return PaymentRequest(**defaults)


class TestParameter:
    def test_to_dict_emits_all_fields_with_defaults(self):
        assert Parameter(name="issuer", value="ABNANL2A").to_dict() == {
            "Name": "issuer",
            "GroupType": "",
            "GroupID": "",
            "Value": "ABNANL2A",
        }

    def test_to_dict_preserves_group_metadata(self):
        assert Parameter(
            name="street", value="Main", group_type="Address", group_id="1"
        ).to_dict() == {
            "Name": "street",
            "GroupType": "Address",
            "GroupID": "1",
            "Value": "Main",
        }


class TestClientIP:
    def test_defaults(self):
        assert ClientIP().to_dict() == {"Type": 0, "Address": "0.0.0.0"}

    def test_custom_values(self):
        assert ClientIP(type=1, address="127.0.0.1").to_dict() == {
            "Type": 1,
            "Address": "127.0.0.1",
        }


class TestService:
    def test_to_dict_without_parameters(self):
        assert Service(name="ideal").to_dict() == {"Name": "ideal", "Action": "Pay"}

    def test_to_dict_with_none_parameters_omits_parameters_key(self):
        result = Service(name="ideal", action="Refund", parameters=None).to_dict()
        assert result == {"Name": "ideal", "Action": "Refund"}

    def test_to_dict_with_dict_parameters_merges_into_service(self):
        assert Service(
            name="creditcard",
            parameters={"Name": "visa", "Version": 0},
        ).to_dict() == {
            "Name": "visa",
            "Action": "Pay",
            "Version": 0,
        }

    def test_to_dict_with_list_of_parameters_serializes_each(self):
        params = [
            Parameter(name="description", value="QR Payment"),
            Parameter(name="amount", value="5.00"),
        ]
        assert Service(name="idealqr", parameters=params).to_dict() == {
            "Name": "idealqr",
            "Action": "Pay",
            "Parameters": [
                {
                    "Name": "description",
                    "GroupType": "",
                    "GroupID": "",
                    "Value": "QR Payment",
                },
                {
                    "Name": "amount",
                    "GroupType": "",
                    "GroupID": "",
                    "Value": "5.00",
                },
            ],
        }

    def test_to_dict_with_empty_dict_parameters_skips_merge(self):
        # Falsy parameters (empty dict) bypass the merge branch.
        assert Service(name="ideal", parameters={}).to_dict() == {
            "Name": "ideal",
            "Action": "Pay",
        }

    def test_add_parameter_accepts_parameter_instance(self):
        service = Service(name="idealqr")
        param = Parameter(name="description", value="QR")
        service.add_parameter(param)
        assert service.parameters == [param]

    def test_add_parameter_coerces_dict_input(self):
        service = Service(name="idealqr")
        service.add_parameter({"name": "amount", "value": "5.00"})
        assert service.parameters == [Parameter(name="amount", value="5.00")]

    def test_add_parameter_appends_to_existing_list(self):
        service = Service(name="idealqr", parameters=[Parameter(name="a", value="1")])
        service.add_parameter({"name": "b", "value": "2"})
        assert service.parameters == [
            Parameter(name="a", value="1"),
            Parameter(name="b", value="2"),
        ]

    def test_add_parameter_prefers_buckaroo_cased_keys(self):
        service = Service(name="idealqr")
        service.add_parameter(
            {
                "Name": "amount",
                "Value": "5.00",
                "GroupType": "Order",
                "GroupID": "1",
            }
        )
        assert service.parameters == [
            Parameter(name="amount", value="5.00", group_type="Order", group_id="1")
        ]

    def test_add_parameter_raises_on_dict_form_parameters(self):
        service = Service(name="ideal", parameters={"Issuer": "ABNANL2A"})
        import pytest

        with pytest.raises(TypeError, match="simple key-value parameters"):
            service.add_parameter(Parameter(name="x", value="y"))


class TestServiceList:
    def test_to_dict_wraps_each_service(self):
        services = ServiceList(services=[Service(name="ideal"), Service(name="paypal")])
        assert services.to_dict() == {
            "ServiceList": [
                {"Name": "ideal", "Action": "Pay"},
                {"Name": "paypal", "Action": "Pay"},
            ]
        }

    def test_to_dict_empty(self):
        assert ServiceList(services=[]).to_dict() == {"ServiceList": []}

    def test_add_appends_service_and_returns_self_for_chaining(self):
        sl = ServiceList(services=[])
        ideal = Service(name="ideal")
        paypal = Service(name="paypal")
        result = sl.add(ideal).add(paypal)
        assert result is sl
        assert sl.services == [ideal, paypal]


class TestPaymentRequest:
    def test_to_dict_minimal_emits_default_client_ip(self):
        request = _make_request()
        result = request.to_dict()
        assert result == {
            "Currency": "EUR",
            "AmountDebit": 10.50,
            "Description": "Order 42",
            "Invoice": "INV-42",
            "ReturnURL": "https://example.com/return",
            "ReturnURLCancel": "https://example.com/cancel",
            "ReturnURLError": "https://example.com/error",
            "ReturnURLReject": "https://example.com/reject",
            "ContinueOnIncomplete": "1",
            "ClientIP": {"Type": 0, "Address": "0.0.0.0"},
        }

    def test_post_init_assigns_default_client_ip(self):
        assert _make_request().client_ip == ClientIP()

    def test_to_dict_preserves_explicit_client_ip(self):
        request = _make_request(client_ip=ClientIP(type=1, address="10.0.0.1"))
        assert request.to_dict()["ClientIP"] == {"Type": 1, "Address": "10.0.0.1"}

    def test_to_dict_includes_push_urls_when_set(self):
        request = _make_request(
            push_url="https://example.com/push",
            push_url_failure="https://example.com/push-fail",
        )
        result = request.to_dict()
        assert result["PushURL"] == "https://example.com/push"
        assert result["PushURLFailure"] == "https://example.com/push-fail"

    def test_to_dict_omits_push_urls_when_absent(self):
        result = _make_request().to_dict()
        assert "PushURL" not in result
        assert "PushURLFailure" not in result

    def test_to_dict_includes_services_when_set(self):
        services = ServiceList(services=[Service(name="ideal")])
        result = _make_request(services=services).to_dict()
        assert result["Services"] == {"ServiceList": [{"Name": "ideal", "Action": "Pay"}]}

    def test_to_dict_omits_services_when_absent(self):
        assert "Services" not in _make_request().to_dict()

    def test_to_dict_omits_client_ip_when_falsy(self):
        request = _make_request()
        request.client_ip = None
        assert "ClientIP" not in request.to_dict()

    def test_to_dict_includes_services_selectable_by_client_when_set(self):
        request = _make_request(services_selectable_by_client="ideal,bancontact")
        assert request.to_dict()["ServicesSelectableByClient"] == "ideal,bancontact"

    def test_to_dict_omits_services_selectable_by_client_when_none(self):
        result = _make_request().to_dict()
        assert "ServicesSelectableByClient" not in result

    def test_to_dict_omits_services_selectable_by_client_when_empty_string(self):
        result = _make_request(services_selectable_by_client="").to_dict()
        assert "ServicesSelectableByClient" not in result


class TestServiceUnsupportedParameters:
    def test_to_dict_ignores_parameters_of_unsupported_type(self):
        # A truthy value that is neither list nor dict should be ignored.
        service = Service(name="ideal", parameters="unexpected")
        assert service.to_dict() == {"Name": "ideal", "Action": "Pay"}
