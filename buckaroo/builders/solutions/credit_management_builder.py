from dataclasses import replace
from typing import Dict, Any, List, Optional
from .solution_builder import SolutionBuilder
from ...models.payment_request import CombinableService, PaymentRequest


class CreditManagementBuilder(SolutionBuilder):
    """Builder for Credit Management solutions (DataRequest-based invoicing)."""

    # Grouped-parameter buckets for the debtor-detail actions. Keyed by the
    # wire group type ("Debtor"/"Person"/...) — the validator matches grouped
    # params by group type, not by individual field name. Populate these via
    # ``add_parameter(name, value, group_type)`` or the ``service_parameters``
    # payload key, e.g. ``{"debtor": {"code": "..."}, "person": {...}}``.
    _DEBTOR_DETAIL_GROUPS: Dict[str, Any] = {
        "Person": {
            "type": dict,
            "required": False,
            "description": "Debtor's individual details (name, gender, ...)",
        },
        "Company": {
            "type": dict,
            "required": False,
            "description": "Debtor's company details (name, VAT, chamber of commerce, ...)",
        },
        "Address": {
            "type": dict,
            "required": False,
            "description": "Debtor's address details",
        },
        "Email": {
            "type": dict,
            "required": False,
            "description": "Debtor's email address",
        },
        "Phone": {
            "type": dict,
            "required": False,
            "description": "Debtor's phone numbers",
        },
    }

    # Debtor identification group, required by every action that identifies
    # a debtor via its "Debtor" group (code, ...).
    _DEBTOR_GROUP: Dict[str, Any] = {
        "Debtor": {
            "type": dict,
            "required": True,
            "description": "Debtor identification group (code, ...)",
        },
    }

    # Scalar fields shared by CreateInvoice and CreateCombinedInvoice.
    # CreateInvoice additionally accepts "poNumber" (see its branch below).
    _INVOICE_FIELDS: Dict[str, Any] = {
        "invoiceDate": {
            "type": str,
            "required": False,
            "description": "Date the invoice was issued",
        },
        "dueDate": {
            "type": str,
            "required": True,
            "description": "Date the invoice payment is due",
        },
        "invoiceAmount": {
            "type": str,
            "required": True,
            "description": "Total invoice amount",
        },
        "invoiceAmountVAT": {
            "type": str,
            "required": False,
            "description": "VAT portion of the invoice amount",
        },
        "schemeKey": {
            "type": str,
            "required": True,
            "description": "Key of the credit management scheme to apply",
        },
        "maxStepIndex": {
            "type": str,
            "required": False,
            "description": "Maximum step index in the collection scheme",
        },
        "allowedServices": {
            "type": str,
            "required": False,
            "description": "CSV of payment services allowed to settle the invoice",
        },
        "applyStartRecurrent": {
            "type": str,
            "required": False,
            "description": "Whether to apply as the start of a recurrent scheme",
        },
    }

    # Article field names (caller-friendly) that need remapping to their
    # AddOrUpdateProductLines wire names. Unlisted article fields (quantity,
    # type, totalAmount, totalVat, vatPercentage) pass through unchanged,
    # arriving on the wire as ``Quantity``, ``Type``, ``Totalamount``,
    # ``Totalvat`` and ``Vatpercentage`` (``.capitalize()``, not camelCase).
    _ARTICLE_FIELD_MAP: Dict[str, str] = {
        "identifier": "ProductId",
        "description": "ProductName",
        "price": "PricePerUnit",
    }

    # Per-action, per-group field renames applied in ``build()`` just before
    # the request is assembled. Keyed by lowercased action, then wire group
    # type, then caller-friendly field name -> wire field name (matched
    # case-insensitively against the already-added ``Parameter``s).
    # DebtorInfo maps the debtor's code to wire name "Debtorcode" (not
    # "Code", unlike AddOrUpdateDebtor/CreateInvoice); as a grouped parameter
    # its wire name is run through ``.capitalize()``, so the camelCase written
    # here does not survive as-is.
    _WIRE_NAMES: Dict[str, Dict[str, Dict[str, str]]] = {
        "debtorinfo": {"Debtor": {"code": "DebtorCode"}},
    }

    def get_service_name(self) -> str:
        """Get the service name for Credit Management."""
        return "CreditManagement3"

    def get_allowed_service_parameters(self, action: str = "CreateInvoice") -> Dict[str, Any]:
        """Get the allowed service parameters for Credit Management based on action."""

        if action.lower() == "addorupdatedebtor":
            return {
                **self._DEBTOR_GROUP,
                **self._DEBTOR_DETAIL_GROUPS,
            }

        if action.lower() == "debtorinfo":
            return {**self._DEBTOR_GROUP}

        if action.lower() in ("resumedebtorfile", "pausedebtorfile"):
            return {
                "debtorFileGuid": {
                    "type": str,
                    "required": True,
                    "description": "GUID of the debtor file",
                },
            }

        if action.lower() in ["createinvoice"]:
            return {
                **self._INVOICE_FIELDS,
                "poNumber": {
                    "type": str,
                    "required": False,
                    "description": "Purchase order number",
                },
                **self._DEBTOR_GROUP,
                **self._DEBTOR_DETAIL_GROUPS,
            }

        if action.lower() in ("pauseinvoice", "unpauseinvoice", "invoiceinfo"):
            # invoice is a top-level request field for these actions (set via
            # .invoice(...) or the top-level "invoice" payload key), not a
            # service parameter — the gateway rejects it as a service param
            # with "Invoice: ParameterMissing".
            return {}

        if action.lower() == "createcombinedinvoice":
            return {
                **self._INVOICE_FIELDS,
                **self._DEBTOR_GROUP,
                **self._DEBTOR_DETAIL_GROUPS,
            }

        if action.lower() == "createcreditnote":
            return {
                "originalInvoiceNumber": {
                    "type": str,
                    "required": True,
                    "description": "Invoice number of the original invoice being credited",
                },
                "invoiceDate": {
                    "type": str,
                    "required": True,
                    "description": "Date of the credit note",
                },
                "invoiceAmount": {
                    "type": str,
                    "required": True,
                    "description": "Amount being credited",
                },
                "invoiceAmountVAT": {
                    "type": str,
                    "required": False,
                    "description": "VAT amount being credited",
                },
                **self._DEBTOR_GROUP,
            }

        if action.lower() == "createpaymentplan":
            return {
                "includedInvoiceKey": {
                    "type": str,
                    "required": True,
                    "description": "Key of the invoice included in the payment plan",
                },
                "dossierNumber": {
                    "type": str,
                    "required": True,
                    "description": "Dossier number for the payment plan",
                },
                "startDate": {
                    "type": str,
                    "required": True,
                    "description": "Date the payment plan starts",
                },
                "interval": {
                    "type": str,
                    "required": True,
                    "description": 'Interval between installments (e.g. "Month")',
                },
                "paymentPlanCostAmount": {
                    "type": str,
                    "required": True,
                    "description": "Cost amount charged for the payment plan",
                },
                "recipientEmail": {
                    "type": str,
                    "required": True,
                    "description": "Email address the payment plan is sent to",
                },
                "installmentCount": {
                    "type": str,
                    "required": False,
                    "description": "Number of installments; either this or "
                    "installmentAmount must be specified",
                },
                "installmentAmount": {
                    "type": str,
                    "required": False,
                    "description": "Amount per installment; either this or "
                    "installmentCount must be specified",
                },
            }

        if action.lower() == "terminatepaymentplan":
            return {
                "includedInvoiceKey": {
                    "type": str,
                    "required": True,
                    "description": "Key of the invoice whose payment plan is terminated",
                },
            }

        if action.lower() == "addorupdateproductlines":
            return {
                "invoiceKey": {
                    "type": str,
                    "required": True,
                    "description": "Key of the invoice to update",
                },
                "ProductLine": {
                    "type": dict,
                    "required": True,
                    "description": "Product line (article) group(s): type, totalAmount, "
                    "totalVat, identifier, description, quantity, price, vatPercentage",
                },
            }

        return {}

    def _with_wire_name(self, param, group_fields: Dict[str, Dict[str, str]]):
        """Return ``param``, or a renamed copy of it if ``_WIRE_NAMES`` matches.

        Never mutates ``param`` itself — callers rely on the original
        parameter surviving unchanged for other actions built from the same
        builder (see ``build`` below).
        """
        field_map = next(
            (
                fields
                for group_type, fields in group_fields.items()
                if group_type.lower() == param.group_type.lower()
            ),
            None,
        )
        if not field_map:
            return param
        wire_name = next(
            (
                wire_name
                for field_name, wire_name in field_map.items()
                if field_name.lower() == param.name.lower()
            ),
            None,
        )
        if not wire_name:
            return param
        return replace(param, name=wire_name.capitalize())

    def build(
        self, action: str = "Pay", validate: bool = True, strict_validation: bool = False
    ) -> PaymentRequest:
        """Build the request, applying ``_WIRE_NAMES`` renames for ``action`` first.

        Runs before every action method (and any direct ``build``/
        ``execute_action`` call), so the rename always applies regardless of
        how the caller reaches this action.

        The rename is applied to a COPY of ``_service_parameters`` for the
        duration of the build, then the original list is restored. Renaming
        in place would leak across actions: a builder reused for
        ``build("DebtorInfo")`` then ``build("AddOrUpdateDebtor")`` would keep
        the "Debtorcode" rename DebtorInfo applies even though
        AddOrUpdateDebtor needs "Code".
        """
        group_fields = self._WIRE_NAMES.get(action.lower(), {})
        original = self._service_parameters
        self._service_parameters = [self._with_wire_name(p, group_fields) for p in original]
        try:
            return super().build(action, validate, strict_validation)
        finally:
            self._service_parameters = original

    def create_invoice(self, validate: bool = True) -> Any:
        """Create an invoice via CreateInvoice.

        ``invoice`` and ``currency`` are TOP-LEVEL request fields, not
        service parameters — set them via ``.invoice(...)``/``.currency(...)``
        or the top-level ``invoice``/``currency`` payload keys (the gateway
        rejects them as service parameters with ``ParameterMissing``).
        Requires ``invoiceAmount``, ``dueDate`` and ``schemeKey`` to be set as
        service parameters, plus a ``Debtor`` group with ``code`` set (via
        ``add_parameter("code", "...", "Debtor")`` or the
        ``service_parameters`` payload key, e.g. ``{"debtor": {"code": "..."}}``).
        Optional ``Person``, ``Company``, ``Address``, ``Email`` and ``Phone``
        groups add debtor details the same way. Raises
        :class:`RequiredParameterMissingError` when a required field is
        missing and ``validate`` is True.
        """
        payload = self.build("CreateInvoice", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def add_or_update_debtor(self, validate: bool = True) -> Any:
        """Create or update a debtor via AddOrUpdateDebtor.

        Requires a ``Debtor`` group with ``code`` set (via
        ``add_parameter("code", "...", "Debtor")`` or the
        ``service_parameters`` payload key, e.g. ``{"debtor": {"code": "..."}}``).
        Optional ``Person``, ``Company``, ``Address``, ``Email`` and ``Phone``
        groups add debtor details the same way. Raises
        :class:`RequiredParameterMissingError` when the ``Debtor`` group is
        missing and ``validate`` is True.
        """
        payload = self.build("AddOrUpdateDebtor", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def debtor_info(self, validate: bool = True) -> Any:
        """Retrieve debtor info via DebtorInfo.

        Requires a ``Debtor`` group with ``code`` set. Raises
        :class:`RequiredParameterMissingError` when missing and ``validate``
        is True.

        Unlike ``AddOrUpdateDebtor``/``CreateInvoice``, DebtorInfo maps the
        debtor's code to wire name ``Debtorcode`` rather than ``Code``; this
        is rewritten automatically (see ``_WIRE_NAMES``) so callers keep
        using ``code``.
        """
        payload = self.build("DebtorInfo", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def resume_debtor_file(self, validate: bool = True) -> Any:
        """Resume a paused debtor file via ResumeDebtorFile.

        Requires ``debtorFileGuid`` to be set. Raises
        :class:`RequiredParameterMissingError` when missing and ``validate``
        is True.
        """
        payload = self.build("ResumeDebtorFile", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def pause_debtor_file(self, validate: bool = True) -> Any:
        """Pause a debtor file via PauseDebtorFile.

        Requires ``debtorFileGuid`` to be set. Raises
        :class:`RequiredParameterMissingError` when missing and ``validate``
        is True.
        """
        payload = self.build("PauseDebtorFile", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def pause_invoice(self, validate: bool = True) -> Any:
        """Pause a single invoice via PauseInvoice.

        ``invoice`` is a TOP-LEVEL request field — set it via
        ``.invoice(...)`` or the top-level ``invoice`` payload key, not as a
        service parameter.
        """
        payload = self.build("PauseInvoice", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def unpause_invoice(self, validate: bool = True) -> Any:
        """Resume a paused invoice via UnPauseInvoice.

        ``invoice`` is a TOP-LEVEL request field — set it via
        ``.invoice(...)`` or the top-level ``invoice`` payload key, not as a
        service parameter.
        """
        payload = self.build("UnPauseInvoice", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def invoice_info(self, validate: bool = True) -> Any:
        """Retrieve invoice info via InvoiceInfo.

        ``invoice`` is a TOP-LEVEL request field — set it via
        ``.invoice(...)`` or the top-level ``invoice`` payload key, not as a
        service parameter.
        """
        payload = self.build("InvoiceInfo", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def create_combined_invoice(self, validate: bool = True) -> CombinableService:
        """Build a CreateCombinedInvoice service to combine into a payment or refund.

        Combine the result into the funding payment or refund, e.g.
        ``payments.create_payment("ideal", {...}).combine(cm).pay()``, so the
        invoice is created in the same request that settles it.

        Only this builder's ``Service`` entry rides along in the combined
        request's ``ServiceList`` — top-level fields set on this builder
        (``invoice``, ``currency``, ...) are discarded. ``invoice`` and
        ``currency`` are still TOP-LEVEL request fields for CreateCombinedInvoice
        (the gateway rejects them as service parameters), but since the
        request has a single shared top level, set them on the *funding*
        payment/refund builder instead (e.g.
        ``payments.create_payment("ideal", {"invoice": "...", ...})``).
        Accepts the same invoice service fields as ``create_invoice``
        (``invoiceAmount``, ``dueDate``, ``schemeKey``, ...) plus a ``Debtor``
        group (and optional ``Person``/``Company``/``Address``/``Email``/
        ``Phone`` groups) in place of a flat debtor ``code``, set via
        ``add_parameter`` or the ``service_parameters`` payload key.

        Args:
            validate: Whether to validate and filter service parameters.
        """
        service = self.build("CreateCombinedInvoice", validate=validate).services.services[0]
        # ``service.parameters`` is this builder's live ``_service_parameters``
        # list (passed by reference in ``BaseBuilder.build``). Copy it so a
        # later ``add_parameter`` call on this builder can't mutate the
        # "already built" combined service.
        service = replace(service, parameters=list(service.parameters or []))
        return CombinableService(services=[service])

    def create_credit_note(self, validate: bool = True) -> Any:
        """Create a credit note via CreateCreditNote.

        ``invoice`` (the credit note's own number) is a TOP-LEVEL request
        field — set it via ``.invoice(...)`` or the top-level ``invoice``
        payload key, not as a service parameter. Requires
        ``originalInvoiceNumber`` (the invoice being credited) and a
        ``Debtor`` group with ``code`` set as service parameters. Raises
        :class:`RequiredParameterMissingError` when any of them are missing
        and ``validate`` is True.
        """
        payload = self.build("CreateCreditNote", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def create_payment_plan(self, validate: bool = True) -> Any:
        """Create a payment plan via CreatePaymentPlan.

        Requires ``includedInvoiceKey``, ``dossierNumber``, ``startDate``,
        ``interval``, ``paymentPlanCostAmount`` and ``recipientEmail`` to be
        set (via ``add_parameter`` or the ``service_parameters`` payload key).
        Also requires either ``installmentCount`` or ``installmentAmount``
        (the gateway rejects the request if neither is given, but the SDK does
        not enforce this choice itself). Raises
        :class:`RequiredParameterMissingError` when a required field is
        missing and ``validate`` is True.

        ``description`` is a TOP-LEVEL request field, not a service parameter
        — set it via ``.description(...)`` or the top-level ``description``
        payload key. The gateway rejects it as an unknown parameter when it is
        sent inside the service's parameter list, and reports "a description is
        required" when it is absent.

        The account must additionally have an active Buckaroo Credit
        Management subscription, and the included invoice must be past its
        due date — these are account/business rules enforced by the gateway,
        not the SDK.
        """
        payload = self.build("CreatePaymentPlan", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def terminate_payment_plan(self, validate: bool = True) -> Any:
        """Terminate a payment plan via TerminatePaymentPlan.

        Requires ``includedInvoiceKey`` to be set. Raises
        :class:`RequiredParameterMissingError` when missing and ``validate``
        is True.
        """
        payload = self.build("TerminatePaymentPlan", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def add_or_update_product_lines(
        self, articles: Optional[List[Dict[str, Any]]] = None, validate: bool = True
    ) -> Any:
        """Add or update an invoice's product lines via AddOrUpdateProductLines.

        Requires ``invoiceKey`` to be set (via ``add_parameter`` or the
        ``service_parameters`` payload key) and at least one article in
        ``articles``. The gateway requires each article to carry ``type``
        (``"Regular"`` for a normal line — ``"Product"`` is invalid),
        ``totalAmount`` (or ``totalAmountExVat``) and ``totalVat``, on top of
        the usual ``identifier``, ``description``, ``quantity`` and ``price``.
        ``vatPercentage`` is also accepted. Each article is emitted as an
        indexed ``ProductLine`` group, one group per article. ``identifier``,
        ``description`` and ``price`` are renamed before hitting the wire
        (``.capitalize()`` then flattens the casing), arriving as
        ``Productid``, ``Productname`` and ``Priceperunit``; the rest
        (``quantity``, ``type``, ``totalAmount``, ``totalVat``,
        ``vatPercentage``) pass through unchanged, arriving on the wire as
        ``Quantity``, ``Type``, ``Totalamount``, ``Totalvat`` and
        ``Vatpercentage``.

        ``articles`` must be passed as this method's argument, not through
        ``service_parameters`` — passing articles via ``service_parameters``
        builds a wrong ``Articles`` group and the gateway will reject it.

        Raises :class:`RequiredParameterMissingError` when ``invoiceKey`` or
        ``articles`` is missing and ``validate`` is True.
        """
        for index, article in enumerate(articles or [], start=1):
            for name, value in article.items():
                wire_name = self._ARTICLE_FIELD_MAP.get(name, name)
                self.add_parameter(wire_name, value, "ProductLine", str(index))

        payload = self.build("AddOrUpdateProductLines", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)
