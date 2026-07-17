"""Unit tests for :class:`CreditManagementBuilder`."""

from __future__ import annotations

import pytest

from buckaroo.builders.solutions.credit_management_builder import CreditManagementBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError
from buckaroo.models.payment_request import CombinableService
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_request


def test_construction_with_client_succeeds(client):
    builder = CreditManagementBuilder(client)
    assert isinstance(builder, CreditManagementBuilder)
    assert isinstance(builder, SolutionBuilder)


def test_get_service_name_returns_credit_management3(client):
    assert CreditManagementBuilder(client).get_service_name() == "CreditManagement3"


def test_get_allowed_service_parameters_create_invoice_marks_required_fields(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("CreateInvoice")

    assert set(params.keys()) == {
        "invoiceDate",
        "dueDate",
        "invoiceAmount",
        "invoiceAmountVAT",
        "schemeKey",
        "maxStepIndex",
        "allowedServices",
        "applyStartRecurrent",
        "poNumber",
        "Debtor",
        "Person",
        "Company",
        "Address",
        "Email",
        "Phone",
    }

    required = {"invoiceAmount", "dueDate", "schemeKey", "Debtor"}
    for name, config in params.items():
        assert config["required"] is (name in required), f"{name} required flag mismatch"


def test_get_allowed_service_parameters_create_invoice_is_case_insensitive(client):
    builder = CreditManagementBuilder(client)
    assert builder.get_allowed_service_parameters("createinvoice") == (
        builder.get_allowed_service_parameters("CreateInvoice")
    )


def test_create_invoice_posts_to_data_request_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "creditmanagement-key-123",
                "Status": {"Code": {"Code": 190}},
                "Services": [
                    {
                        "Name": "CreditManagement3",
                        "Action": "CreateInvoice",
                        "Parameters": [
                            {"Name": "InvoiceKey", "Value": "INVK-001"},
                        ],
                    }
                ],
            },
        )
    )

    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    builder.currency("EUR")
    builder.add_parameter("invoiceAmount", "100.00")
    builder.add_parameter("dueDate", "2026-08-01")
    builder.add_parameter("schemeKey", "SCHEME-1")
    builder.add_parameter("code", "DEBTOR-001", "Debtor")
    response = builder.create_invoice()

    assert response.key == "creditmanagement-key-123"
    assert response.get_service_parameter("InvoiceKey") == "INVK-001"
    assert recorded_action(mock_strategy) == "CreateInvoice"


def test_create_invoice_raises_when_debtor_code_missing(client):
    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    builder.add_parameter("invoiceAmount", "100.00")
    builder.add_parameter("dueDate", "2026-08-01")
    builder.add_parameter("schemeKey", "SCHEME-1")

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.create_invoice()

    assert exc.value.parameter_name == "Debtor"


def test_create_invoice_posts_invoice_and_currency_as_top_level_fields(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-124", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    builder.currency("EUR")
    builder.add_parameter("invoiceAmount", "100.00")
    builder.add_parameter("dueDate", "2026-08-01")
    builder.add_parameter("schemeKey", "SCHEME-1")
    builder.add_parameter("code", "DEBTOR-001", "Debtor")
    response = builder.create_invoice()

    assert response.key == "creditmanagement-key-124"
    assert recorded_action(mock_strategy) == "CreateInvoice"

    request = recorded_request(mock_strategy)
    assert request["Invoice"] == "INV-001"
    assert request["Currency"] == "EUR"

    service = request["Services"]["ServiceList"][0]
    params = {(p["Name"], p["GroupType"]): p["Value"] for p in service["Parameters"]}
    assert params[("Code", "Debtor")] == "DEBTOR-001"
    assert ("Invoice", "") not in params
    assert ("Currency", "") not in params


def test_get_allowed_service_parameters_add_or_update_debtor_declares_groups(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("AddOrUpdateDebtor")

    assert set(params.keys()) == {
        "Debtor",
        "Person",
        "Company",
        "Address",
        "Email",
        "Phone",
    }
    for name, config in params.items():
        assert config["type"] is dict
        assert config["required"] is (name == "Debtor")


def test_get_allowed_service_parameters_debtor_info_declares_required_debtor_group(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("DebtorInfo")

    assert set(params.keys()) == {"Debtor"}
    assert params["Debtor"]["type"] is dict
    assert params["Debtor"]["required"] is True


@pytest.mark.parametrize("action", ["ResumeDebtorFile", "PauseDebtorFile"])
def test_get_allowed_service_parameters_debtor_file_actions_require_debtor_file_guid(
    client, action
):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters(action)

    assert set(params.keys()) == {"debtorFileGuid"}
    assert params["debtorFileGuid"]["required"] is True


def test_add_or_update_debtor_posts_grouped_params_to_data_request(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "creditmanagement-key-456",
                "Status": {"Code": {"Code": 190}},
                "Services": [],
            },
        )
    )

    builder = CreditManagementBuilder(client)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")
    builder.add_parameter("firstName", "John", "Person")
    builder.add_parameter("email", "john@example.com", "Email")
    response = builder.add_or_update_debtor()

    assert response.key == "creditmanagement-key-456"
    assert recorded_action(mock_strategy) == "AddOrUpdateDebtor"

    service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
    params = {(p["Name"], p["GroupType"], p["GroupID"]): p["Value"] for p in service["Parameters"]}
    assert params[("Code", "Debtor", "")] == "DEBTOR-001"
    assert params[("Firstname", "Person", "")] == "John"
    assert params[("Email", "Email", "")] == "john@example.com"


def test_add_or_update_debtor_raises_when_debtor_group_missing(client):
    builder = CreditManagementBuilder(client)
    builder.add_parameter("firstName", "John", "Person")

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.add_or_update_debtor()

    assert exc.value.parameter_name == "Debtor"


def test_debtor_info_posts_debtor_group_to_data_request(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "creditmanagement-key-789",
                "Status": {"Code": {"Code": 190}},
                "Services": [
                    {
                        "Name": "CreditManagement3",
                        "Action": "DebtorInfo",
                        "Parameters": [{"Name": "DebtorKey", "Value": "DEBK-001"}],
                    }
                ],
            },
        )
    )

    builder = CreditManagementBuilder(client)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")
    response = builder.debtor_info()

    assert response.get_service_parameter("DebtorKey") == "DEBK-001"
    assert recorded_action(mock_strategy) == "DebtorInfo"

    service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
    params = {(p["Name"], p["GroupType"], p["GroupID"]): p["Value"] for p in service["Parameters"]}
    # DebtorInfo maps the debtor code to wire name "Debtorcode" (not "Code",
    # unlike AddOrUpdateDebtor/CreateInvoice).
    assert params[("Debtorcode", "Debtor", "")] == "DEBTOR-001"


def test_debtor_info_raises_when_debtor_group_missing(client):
    builder = CreditManagementBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.debtor_info()

    assert exc.value.parameter_name == "Debtor"


def test_build_debtorinfo_directly_renames_debtor_code_without_calling_debtor_info(client):
    # The rename must live in build() itself, not only in debtor_info(), so
    # callers who go through build("DebtorInfo") or execute_action("DebtorInfo")
    # directly still get the correct wire name.
    builder = CreditManagementBuilder(client)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")

    payload = builder.build("DebtorInfo")

    service = payload.services.services[0]
    params = {(p.name, p.group_type): p.value for p in service.parameters}
    assert params[("Debtorcode", "Debtor")] == "DEBTOR-001"


def test_build_debtorinfo_rename_is_idempotent_across_repeated_build_calls(client):
    builder = CreditManagementBuilder(client)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")

    builder.build("DebtorInfo")
    payload = builder.build("DebtorInfo")

    service = payload.services.services[0]
    params = [(p.name, p.group_type) for p in service.parameters]
    assert params.count(("Debtorcode", "Debtor")) == 1


def test_build_debtorinfo_then_addorupdatedebtor_does_not_leak_renamed_parameter_name(client):
    # build("DebtorInfo") must not mutate the builder's own parameter list in
    # place: a subsequent build("AddOrUpdateDebtor") on the SAME builder needs
    # "Code" on the wire, not the "Debtorcode" rename DebtorInfo applies.
    builder = CreditManagementBuilder(client)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")

    builder.build("DebtorInfo")
    payload = builder.build("AddOrUpdateDebtor")

    service = payload.services.services[0]
    params = {(p.name, p.group_type): p.value for p in service.parameters}
    assert params[("Code", "Debtor")] == "DEBTOR-001"
    assert ("Debtorcode", "Debtor") not in params


def test_build_addorupdatedebtor_then_debtorinfo_still_renames_correctly(client):
    # Reverse order: an unaffected action first must not prevent DebtorInfo's
    # own rename from applying afterwards.
    builder = CreditManagementBuilder(client)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")

    builder.build("AddOrUpdateDebtor")
    payload = builder.build("DebtorInfo")

    service = payload.services.services[0]
    params = {(p.name, p.group_type): p.value for p in service.parameters}
    assert params[("Debtorcode", "Debtor")] == "DEBTOR-001"
    assert ("Code", "Debtor") not in params


@pytest.mark.parametrize(
    "method_name,action",
    [
        ("resume_debtor_file", "ResumeDebtorFile"),
        ("pause_debtor_file", "PauseDebtorFile"),
    ],
)
def test_debtor_file_actions_post_debtor_file_guid_to_data_request(
    client, mock_strategy, method_name, action
):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-321", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.add_parameter("debtorFileGuid", "FILE-GUID-001")
    response = getattr(builder, method_name)()

    assert response.key == "creditmanagement-key-321"
    assert recorded_action(mock_strategy) == action

    service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
    params = {p["Name"]: p["Value"] for p in service["Parameters"]}
    assert params["Debtorfileguid"] == "FILE-GUID-001"


@pytest.mark.parametrize("method_name", ["resume_debtor_file", "pause_debtor_file"])
def test_debtor_file_actions_raise_when_debtor_file_guid_missing(client, method_name):
    builder = CreditManagementBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        getattr(builder, method_name)()

    assert exc.value.parameter_name == "debtorFileGuid"


@pytest.mark.parametrize("action", ["PauseInvoice", "UnPauseInvoice", "InvoiceInfo"])
def test_get_allowed_service_parameters_invoice_actions_declare_no_service_parameters(
    client, action
):
    # invoice is a top-level request field for these actions, not a service
    # parameter, so there is nothing left to declare.
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters(action)

    assert params == {}


@pytest.mark.parametrize(
    "method_name,action",
    [
        ("pause_invoice", "PauseInvoice"),
        ("unpause_invoice", "UnPauseInvoice"),
        ("invoice_info", "InvoiceInfo"),
    ],
)
def test_invoice_actions_post_invoice_as_top_level_field(
    client, mock_strategy, method_name, action
):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-654", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    response = getattr(builder, method_name)()

    assert response.key == "creditmanagement-key-654"
    assert recorded_action(mock_strategy) == action

    request = recorded_request(mock_strategy)
    assert request["Invoice"] == "INV-001"


def test_get_allowed_service_parameters_create_credit_note_declares_fields(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("CreateCreditNote")

    assert set(params.keys()) == {
        "originalInvoiceNumber",
        "invoiceDate",
        "invoiceAmount",
        "invoiceAmountVAT",
        "Debtor",
    }
    assert params["originalInvoiceNumber"]["required"] is True
    assert params["invoiceDate"]["required"] is True
    assert params["invoiceAmount"]["required"] is True
    assert params["invoiceAmountVAT"]["required"] is False
    assert params["Debtor"]["type"] is dict
    assert params["Debtor"]["required"] is True


def test_create_credit_note_posts_invoice_top_level_and_debtor_group_to_data_request(
    client, mock_strategy
):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-987", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.invoice("CN-001")
    builder.add_parameter("originalInvoiceNumber", "INV-001")
    builder.add_parameter("invoiceDate", "2026-07-16")
    builder.add_parameter("invoiceAmount", 10.00)
    builder.add_parameter("code", "DEBTOR-001", "Debtor")
    response = builder.create_credit_note()

    assert response.key == "creditmanagement-key-987"
    assert recorded_action(mock_strategy) == "CreateCreditNote"

    request = recorded_request(mock_strategy)
    assert request["Invoice"] == "CN-001"

    service = request["Services"]["ServiceList"][0]
    params = {(p["Name"], p["GroupType"]): p["Value"] for p in service["Parameters"]}
    assert params[("Originalinvoicenumber", "")] == "INV-001"
    assert params[("Invoicedate", "")] == "2026-07-16"
    assert params[("Invoiceamount", "")] == "10.0"
    assert params[("Code", "Debtor")] == "DEBTOR-001"


def test_create_credit_note_raises_when_debtor_group_missing(client):
    builder = CreditManagementBuilder(client)
    builder.invoice("CN-001")
    builder.add_parameter("originalInvoiceNumber", "INV-001")
    builder.add_parameter("invoiceDate", "2026-07-16")
    builder.add_parameter("invoiceAmount", 10.00)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.create_credit_note()

    assert exc.value.parameter_name == "Debtor"


def test_get_allowed_service_parameters_add_or_update_product_lines_declares_fields(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("AddOrUpdateProductLines")

    assert set(params.keys()) == {"invoiceKey", "ProductLine"}
    assert params["invoiceKey"]["required"] is True
    assert params["ProductLine"]["type"] is dict
    assert params["ProductLine"]["required"] is True


def test_add_or_update_product_lines_posts_indexed_grouped_articles(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-111", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.add_parameter("invoiceKey", "INVK-001")
    response = builder.add_or_update_product_lines(
        articles=[
            {
                "identifier": "SKU-1",
                "description": "Widget",
                "quantity": "2",
                "price": "10.00",
                "type": "Regular",
                "totalAmount": "20.00",
                "totalVat": "4.20",
                "vatPercentage": "21",
            },
            {"identifier": "SKU-2", "description": "Gadget", "quantity": "1", "price": "25.00"},
        ]
    )

    assert response.key == "creditmanagement-key-111"
    assert recorded_action(mock_strategy) == "AddOrUpdateProductLines"

    service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
    params = {(p["Name"], p["GroupType"], p["GroupID"]): p["Value"] for p in service["Parameters"]}
    assert params[("Invoicekey", "", "")] == "INVK-001"
    assert params[("Productid", "ProductLine", "1")] == "SKU-1"
    assert params[("Productname", "ProductLine", "1")] == "Widget"
    assert params[("Quantity", "ProductLine", "1")] == "2"
    assert params[("Priceperunit", "ProductLine", "1")] == "10.00"
    assert params[("Type", "ProductLine", "1")] == "Regular"
    assert params[("Totalamount", "ProductLine", "1")] == "20.00"
    assert params[("Totalvat", "ProductLine", "1")] == "4.20"
    assert params[("Vatpercentage", "ProductLine", "1")] == "21"
    assert params[("Productid", "ProductLine", "2")] == "SKU-2"
    assert params[("Productname", "ProductLine", "2")] == "Gadget"
    assert params[("Quantity", "ProductLine", "2")] == "1"
    assert params[("Priceperunit", "ProductLine", "2")] == "25.00"


def test_add_or_update_product_lines_raises_when_articles_missing(client):
    builder = CreditManagementBuilder(client)
    builder.add_parameter("invoiceKey", "INVK-001")

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.add_or_update_product_lines()

    assert exc.value.parameter_name == "ProductLine"


def test_get_allowed_service_parameters_create_combined_invoice_declares_fields(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("CreateCombinedInvoice")

    assert set(params.keys()) == {
        "invoiceDate",
        "dueDate",
        "invoiceAmount",
        "invoiceAmountVAT",
        "schemeKey",
        "maxStepIndex",
        "allowedServices",
        "applyStartRecurrent",
        "Debtor",
        "Person",
        "Company",
        "Address",
        "Email",
        "Phone",
    }

    required = {"invoiceAmount", "dueDate", "schemeKey", "Debtor"}
    for name, config in params.items():
        assert config["required"] is (name in required), f"{name} required flag mismatch"


def test_create_combined_invoice_returns_combinable_service_without_posting(client, mock_strategy):
    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    builder.add_parameter("invoiceAmount", "100.00")
    builder.add_parameter("dueDate", "2026-08-01")
    builder.add_parameter("schemeKey", "SCHEME-1")
    builder.add_parameter("code", "DEBTOR-001", "Debtor")

    combinable = builder.create_combined_invoice()

    assert isinstance(combinable, CombinableService)
    assert len(combinable.services) == 1
    service = combinable.services[0]
    assert service.name == "CreditManagement3"
    assert service.action == "CreateCombinedInvoice"
    assert mock_strategy.calls == []


def test_create_combined_invoice_service_parameters_are_not_mutated_by_later_add_parameter(
    client,
):
    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    builder.add_parameter("invoiceAmount", "100.00")
    builder.add_parameter("dueDate", "2026-08-01")
    builder.add_parameter("schemeKey", "SCHEME-1")
    builder.add_parameter("code", "DEBTOR-001", "Debtor")

    combinable = builder.create_combined_invoice()
    service = combinable.services[0]
    param_count_before = len(service.parameters)

    # Mutating the builder after the combined service was "already built"
    # must not leak into the returned service's parameter list.
    builder.add_parameter("extraField", "extra-value")

    assert len(service.parameters) == param_count_before


def test_create_combined_invoice_raises_when_debtor_group_missing(client):
    builder = CreditManagementBuilder(client)
    builder.invoice("INV-001")
    builder.add_parameter("invoiceAmount", "100.00")
    builder.add_parameter("dueDate", "2026-08-01")
    builder.add_parameter("schemeKey", "SCHEME-1")

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.create_combined_invoice()

    assert exc.value.parameter_name == "Debtor"


def test_get_allowed_service_parameters_create_payment_plan_declares_fields(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("CreatePaymentPlan")

    assert set(params.keys()) == {
        "includedInvoiceKey",
        "dossierNumber",
        "startDate",
        "interval",
        "paymentPlanCostAmount",
        "recipientEmail",
        "installmentCount",
        "installmentAmount",
    }

    required = {
        "includedInvoiceKey",
        "dossierNumber",
        "startDate",
        "interval",
        "paymentPlanCostAmount",
        "recipientEmail",
    }
    for name, config in params.items():
        assert config["required"] is (name in required), f"{name} required flag mismatch"


def test_get_allowed_service_parameters_create_payment_plan_excludes_description(client):
    # description is a TOP-LEVEL request field for CreatePaymentPlan (like
    # invoice/currency for the invoice actions), never a service parameter —
    # the gateway rejects it with 491 "Description is not a known parameter"
    # when sent as one.
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("CreatePaymentPlan")

    assert "description" not in params


def test_create_payment_plan_posts_to_data_request(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-222", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.description("3-month plan")
    builder.add_parameter("includedInvoiceKey", "INVK-001")
    builder.add_parameter("dossierNumber", "DOSSIER-1")
    builder.add_parameter("startDate", "2026-09-01")
    builder.add_parameter("interval", "Month")
    builder.add_parameter("paymentPlanCostAmount", "5.00")
    builder.add_parameter("recipientEmail", "debtor@example.com")
    builder.add_parameter("installmentCount", "3")
    response = builder.create_payment_plan()

    assert response.key == "creditmanagement-key-222"
    assert recorded_action(mock_strategy) == "CreatePaymentPlan"

    request = recorded_request(mock_strategy)
    assert request["Description"] == "3-month plan"

    service = request["Services"]["ServiceList"][0]
    params = {p["Name"]: p["Value"] for p in service["Parameters"]}
    assert params["Includedinvoicekey"] == "INVK-001"
    assert params["Dossiernumber"] == "DOSSIER-1"
    assert params["Startdate"] == "2026-09-01"
    assert params["Interval"] == "Month"
    assert params["Paymentplancostamount"] == "5.00"
    assert params["Recipientemail"] == "debtor@example.com"
    assert params["Installmentcount"] == "3"
    assert "Description" not in params


def test_create_payment_plan_raises_when_included_invoice_key_missing(client):
    builder = CreditManagementBuilder(client)
    builder.description("3-month plan")
    builder.add_parameter("dossierNumber", "DOSSIER-1")
    builder.add_parameter("startDate", "2026-09-01")
    builder.add_parameter("interval", "Month")
    builder.add_parameter("paymentPlanCostAmount", "5.00")
    builder.add_parameter("recipientEmail", "debtor@example.com")

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.create_payment_plan()

    assert exc.value.parameter_name == "includedInvoiceKey"


def test_get_allowed_service_parameters_terminate_payment_plan_declares_fields(client):
    builder = CreditManagementBuilder(client)
    params = builder.get_allowed_service_parameters("TerminatePaymentPlan")

    assert set(params.keys()) == {"includedInvoiceKey"}
    assert params["includedInvoiceKey"]["required"] is True


def test_terminate_payment_plan_posts_to_data_request(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "creditmanagement-key-333", "Status": {"Code": {"Code": 190}}, "Services": []},
        )
    )

    builder = CreditManagementBuilder(client)
    builder.add_parameter("includedInvoiceKey", "INVK-001")
    response = builder.terminate_payment_plan()

    assert response.key == "creditmanagement-key-333"
    assert recorded_action(mock_strategy) == "TerminatePaymentPlan"

    service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
    params = {p["Name"]: p["Value"] for p in service["Parameters"]}
    assert params["Includedinvoicekey"] == "INVK-001"


def test_terminate_payment_plan_raises_when_included_invoice_key_missing(client):
    builder = CreditManagementBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.terminate_payment_plan()

    assert exc.value.parameter_name == "includedInvoiceKey"
