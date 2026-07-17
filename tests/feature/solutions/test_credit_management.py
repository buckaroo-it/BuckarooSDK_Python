import pytest

from buckaroo.exceptions._parameter_validation_error import (
    ParameterValidationError,
    RequiredParameterMissingError,
)
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers
from tests.support.recording_mock import (
    recorded_action,
    recorded_request,
    recorded_service_parameters,
)


class TestCreditManagementFeature:
    """Feature tests for the Credit Management solution."""

    def test_credit_management_is_available(self, buckaroo):
        assert buckaroo.solutions.is_method_supported("creditmanagement")

    def test_create_invoice_posts_service_parameters_and_returns_invoice_key(
        self, buckaroo, mock_strategy
    ):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "CreditManagement3",
                        "Action": "CreateInvoice",
                        "Parameters": [{"Name": "InvoiceKey", "Value": "INVK-999"}],
                    }
                ],
                "ServiceCode": "CreditManagement3",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "invoice": "INV-999",
                "currency": "EUR",
                "service_parameters": {
                    "invoiceAmount": "250.00",
                    "dueDate": "2026-09-01",
                    "schemeKey": "SCHEME-2",
                    "debtor": {"code": "DEBTOR-999"},
                },
            },
        ).create_invoice()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert response.get_service_parameter("InvoiceKey") == "INVK-999"
        assert recorded_action(mock_strategy) == "CreateInvoice"

        # invoice/currency are top-level request fields, not service
        # parameters — the gateway rejects them as service params.
        request = recorded_request(mock_strategy)
        assert request["Invoice"] == "INV-999"
        assert request["Currency"] == "EUR"

        params = {
            (p["Name"], p["GroupType"]): p["Value"]
            for p in recorded_service_parameters(mock_strategy)
        }
        assert ("Invoice", "") not in params
        assert ("Currency", "") not in params
        assert params[("Invoiceamount", "")] == "250.00"
        assert params[("Duedate", "")] == "2026-09-01"
        assert params[("Schemekey", "")] == "SCHEME-2"
        assert params[("Code", "Debtor")] == "DEBTOR-999"

    def test_create_invoice_without_required_params_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution("creditmanagement")

        with pytest.raises(ParameterValidationError):
            builder.create_invoice()

    def test_create_invoice_without_debtor_code_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "invoice": "INV-1",
                "service_parameters": {
                    "invoiceAmount": "10.00",
                    "dueDate": "2026-09-01",
                    "schemeKey": "SCHEME-1",
                },
            },
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.create_invoice()

        assert exc.value.parameter_name == "Debtor"

    def test_add_or_update_debtor_posts_grouped_debtor_details(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "CreditManagement3",
                        "Action": "AddOrUpdateDebtor",
                        "Parameters": [{"Name": "DebtorKey", "Value": "DEBK-999"}],
                    }
                ],
                "ServiceCode": "CreditManagement3",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "service_parameters": {
                    "debtor": {"code": "DEBTOR-999"},
                    "person": {"firstName": "John", "lastName": "Doe"},
                    "address": {"street": "Main St", "city": "Amsterdam"},
                    "email": {"email": "john@example.com"},
                }
            },
        ).add_or_update_debtor()

        assert response.status.code.code == 190
        assert response.get_service_parameter("DebtorKey") == "DEBK-999"
        assert recorded_action(mock_strategy) == "AddOrUpdateDebtor"

        params = {
            (p["Name"], p["GroupType"]): p["Value"]
            for p in recorded_service_parameters(mock_strategy)
        }
        assert params[("Code", "Debtor")] == "DEBTOR-999"
        assert params[("Firstname", "Person")] == "John"
        assert params[("Lastname", "Person")] == "Doe"
        assert params[("Street", "Address")] == "Main St"
        assert params[("City", "Address")] == "Amsterdam"
        assert params[("Email", "Email")] == "john@example.com"

    def test_add_or_update_debtor_without_debtor_group_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"person": {"firstName": "John"}}},
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.add_or_update_debtor()

        assert exc.value.parameter_name == "Debtor"

    def test_debtor_info_posts_debtor_code_and_returns_details(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "CreditManagement3",
                        "Action": "DebtorInfo",
                        "Parameters": [{"Name": "Status", "Value": "Active"}],
                    }
                ],
                "ServiceCode": "CreditManagement3",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"debtor": {"code": "DEBTOR-999"}}},
        ).debtor_info()

        assert response.get_service_parameter("Status") == "Active"
        assert recorded_action(mock_strategy) == "DebtorInfo"
        params = {
            (p["Name"], p["GroupType"]): p["Value"]
            for p in recorded_service_parameters(mock_strategy)
        }
        assert params[("Debtorcode", "Debtor")] == "DEBTOR-999"

    @pytest.mark.parametrize(
        "method_name,action",
        [
            ("resume_debtor_file", "ResumeDebtorFile"),
            ("pause_debtor_file", "PauseDebtorFile"),
        ],
    )
    def test_debtor_file_actions_post_debtor_file_guid(
        self, buckaroo, mock_strategy, method_name, action
    ):
        response_body = Helpers.success_response(
            {"Services": [], "ServiceCode": "CreditManagement3"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"debtorFileGuid": "FILE-GUID-999"}},
        )
        response = getattr(builder, method_name)()

        assert response.status.code.code == 190
        assert recorded_action(mock_strategy) == action
        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["Debtorfileguid"] == "FILE-GUID-999"

    @pytest.mark.parametrize("method_name", ["resume_debtor_file", "pause_debtor_file"])
    def test_debtor_file_actions_without_debtor_file_guid_raise_before_wire(
        self, buckaroo, method_name
    ):
        builder = buckaroo.solutions.create_solution("creditmanagement")

        with pytest.raises(RequiredParameterMissingError) as exc:
            getattr(builder, method_name)()

        assert exc.value.parameter_name == "debtorFileGuid"

    @pytest.mark.parametrize(
        "method_name,action",
        [
            ("pause_invoice", "PauseInvoice"),
            ("unpause_invoice", "UnPauseInvoice"),
            ("invoice_info", "InvoiceInfo"),
        ],
    )
    def test_invoice_actions_post_invoice(self, buckaroo, mock_strategy, method_name, action):
        response_body = Helpers.success_response(
            {"Services": [], "ServiceCode": "CreditManagement3"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        # invoice is a top-level request field for these actions, not a
        # service parameter.
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"invoice": "INV-999"},
        )
        response = getattr(builder, method_name)()

        assert response.status.code.code == 190
        assert recorded_action(mock_strategy) == action
        request = recorded_request(mock_strategy)
        assert request["Invoice"] == "INV-999"

    def test_create_credit_note_posts_original_invoice_and_debtor(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {"Services": [], "ServiceCode": "CreditManagement3"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "invoice": "CN-001",
                "service_parameters": {
                    "originalInvoiceNumber": "INV-999",
                    "invoiceDate": "2026-07-16",
                    "invoiceAmount": 10.00,
                    "debtor": {"code": "DEBTOR-999"},
                },
            },
        ).create_credit_note()

        assert response.status.code.code == 190
        assert recorded_action(mock_strategy) == "CreateCreditNote"

        request = recorded_request(mock_strategy)
        assert request["Invoice"] == "CN-001"

        params = {
            (p["Name"], p["GroupType"]): p["Value"]
            for p in recorded_service_parameters(mock_strategy)
        }
        assert ("Invoice", "") not in params
        assert params[("Originalinvoicenumber", "")] == "INV-999"
        assert params[("Code", "Debtor")] == "DEBTOR-999"

    def test_create_credit_note_without_debtor_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "invoice": "CN-001",
                "service_parameters": {
                    "originalInvoiceNumber": "INV-999",
                    "invoiceDate": "2026-07-16",
                    "invoiceAmount": 10.00,
                },
            },
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.create_credit_note()

        assert exc.value.parameter_name == "Debtor"

    def test_add_or_update_product_lines_posts_indexed_articles(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {"Services": [], "ServiceCode": "CreditManagement3"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"invoiceKey": "INVK-999"}},
        )
        response = builder.add_or_update_product_lines(
            articles=[
                {"identifier": "SKU-1", "description": "Widget", "quantity": "2", "price": "10.00"},
            ]
        )

        assert response.status.code.code == 190
        assert recorded_action(mock_strategy) == "AddOrUpdateProductLines"
        params = {
            (p["Name"], p["GroupType"], p["GroupID"]): p["Value"]
            for p in recorded_service_parameters(mock_strategy)
        }
        assert params[("Invoicekey", "", "")] == "INVK-999"
        assert params[("Productid", "ProductLine", "1")] == "SKU-1"
        assert params[("Productname", "ProductLine", "1")] == "Widget"
        assert params[("Quantity", "ProductLine", "1")] == "2"
        assert params[("Priceperunit", "ProductLine", "1")] == "10.00"

    def test_add_or_update_product_lines_without_articles_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"invoiceKey": "INVK-999"}},
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.add_or_update_product_lines()

        assert exc.value.parameter_name == "ProductLine"

    def test_create_payment_plan_posts_installment_and_dossier_fields(
        self, buckaroo, mock_strategy
    ):
        response_body = Helpers.success_response(
            {"Services": [], "ServiceCode": "CreditManagement3"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                # description is a top-level request field for
                # CreatePaymentPlan, not a service parameter — the gateway
                # rejects it as an unknown parameter when sent as one.
                "description": "3-month plan",
                "service_parameters": {
                    "includedInvoiceKey": "INVK-999",
                    "dossierNumber": "DOSSIER-999",
                    "startDate": "2026-09-01",
                    "interval": "Month",
                    "paymentPlanCostAmount": "5.00",
                    "recipientEmail": "debtor@example.com",
                    "installmentCount": "3",
                },
            },
        ).create_payment_plan()

        assert response.status.code.code == 190
        assert recorded_action(mock_strategy) == "CreatePaymentPlan"

        request = recorded_request(mock_strategy)
        assert request["Description"] == "3-month plan"

        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["Includedinvoicekey"] == "INVK-999"
        assert params["Dossiernumber"] == "DOSSIER-999"
        assert params["Startdate"] == "2026-09-01"
        assert params["Interval"] == "Month"
        assert params["Paymentplancostamount"] == "5.00"
        assert params["Recipientemail"] == "debtor@example.com"
        assert params["Installmentcount"] == "3"
        assert "Description" not in params

    def test_create_payment_plan_without_included_invoice_key_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "description": "3-month plan",
                "service_parameters": {
                    "dossierNumber": "DOSSIER-999",
                    "startDate": "2026-09-01",
                    "interval": "Month",
                    "paymentPlanCostAmount": "5.00",
                    "recipientEmail": "debtor@example.com",
                },
            },
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.create_payment_plan()

        assert exc.value.parameter_name == "includedInvoiceKey"

    def test_terminate_payment_plan_posts_included_invoice_key(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {"Services": [], "ServiceCode": "CreditManagement3"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "creditmanagement",
            {"service_parameters": {"includedInvoiceKey": "INVK-999"}},
        ).terminate_payment_plan()

        assert response.status.code.code == 190
        assert recorded_action(mock_strategy) == "TerminatePaymentPlan"
        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["Includedinvoicekey"] == "INVK-999"

    def test_terminate_payment_plan_without_included_invoice_key_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution("creditmanagement")

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.terminate_payment_plan()

        assert exc.value.parameter_name == "includedInvoiceKey"


class TestCreditManagementCombinedInvoice:
    """CreateCombinedInvoice rides on a payment via combine(), like Marketplaces."""

    def test_create_combined_invoice_combines_into_ideal_pay(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "CreditManagement3",
                        "Action": None,
                        "Parameters": [{"Name": "InvoiceKey", "Value": "INVK-COMBINED-1"}],
                    },
                    {"Name": "ideal", "Action": None, "Parameters": []},
                ],
                "ServiceCode": "ideal",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        # invoice/currency are top-level request fields, and the combined
        # request has a single shared top level — so they're set on the
        # funding payment (below), not on the CreditManagement3 sub-builder.
        cm = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "service_parameters": {
                    "invoiceAmount": "95.00",
                    "dueDate": "2026-09-01",
                    "schemeKey": "SCHEME-1",
                    "debtor": {"code": "DEBTOR-999"},
                }
            },
        ).create_combined_invoice()

        payload = Helpers.standard_payload(
            invoice="INV-COMBINED-1",
            amount=95.00,
            service_parameters={"issuer": "ABNANL2A"},
        )
        response = buckaroo.payments.create_payment("ideal", payload).combine(cm).pay()

        body = recorded_request(mock_strategy)
        assert body["Invoice"] == "INV-COMBINED-1"

        services = body["Services"]["ServiceList"]
        # Payment method first, combined CreditManagement3 service second.
        assert [s["Name"] for s in services] == ["ideal", "CreditManagement3"]
        assert services[0]["Action"] == "Pay"
        assert services[1]["Action"] == "CreateCombinedInvoice"

        invoice_params = {
            (p["Name"], p["GroupType"]): p["Value"] for p in services[1]["Parameters"]
        }
        assert ("Invoice", "") not in invoice_params
        assert invoice_params[("Invoiceamount", "")] == "95.00"
        assert invoice_params[("Code", "Debtor")] == "DEBTOR-999"

        assert response.get_service_parameter("InvoiceKey") == "INVK-COMBINED-1"

    def test_create_combined_invoice_without_debtor_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution(
            "creditmanagement",
            {
                "service_parameters": {
                    "invoiceAmount": "10.00",
                    "dueDate": "2026-09-01",
                    "schemeKey": "SCHEME-1",
                }
            },
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.create_combined_invoice()

        assert exc.value.parameter_name == "Debtor"
