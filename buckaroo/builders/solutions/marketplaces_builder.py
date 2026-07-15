from typing import Any, Dict, Optional

from .solution_builder import SolutionBuilder
from ...models.payment_request import CombinableService
from ...models.payment_response import PaymentResponse


class MarketplacesBuilder(SolutionBuilder):
    """Builder for the Split Payments (``Marketplaces``) solution.

    Marketplaces lets a platform divide one customer payment across its own
    funds account and one or more seller accounts, move held funds later, refund
    from sellers, and move funds between accounts manually.

    ``split`` and ``refund_supplementary`` build a supplementary service that is
    *combined* into a payment or refund (``builder.combine(...).pay()`` /
    ``.refund()``), mirroring the PHP/Node SDKs. ``transfer`` and
    ``manual_transfer`` are standalone data requests.

    The split spec is a single dict:
    ``{"daysUntilTransfer": ..., "marketplace": {...}, "sellers": [{...}, ...]}``
    — ``marketplace`` becomes the funds-account group, each ``sellers`` entry a
    ``Seller`` group with a unique GroupID.
    """

    # Grouped-parameter buckets shared by the split-defining actions. Keyed by
    # the wire group type ("Marketplace"/"Seller") — the validator matches
    # grouped params by group type, not by individual field name.
    _SPLIT_GROUPS: Dict[str, Any] = {
        "Marketplace": {
            "type": dict,
            "required": False,
            "description": "Split group reserved for the Split Payments funds account",
        },
        "Seller": {
            "type": dict,
            "required": False,
            "description": "Split group reserved for a third-party (seller) account",
        },
    }

    def get_service_name(self) -> str:
        """Get the service name for Split Payments."""
        return "Marketplaces"

    def get_allowed_service_parameters(self, action: str = "Split") -> Dict[str, Any]:
        """Get the allowed service parameters for Marketplaces based on action.

        ``marketplace`` and ``sellers`` are grouped-parameter buckets;
        ``DaysUntilTransfer`` is a plain parameter allowed only on ``Split`` (a
        Transfer is always immediate).
        """
        if action.lower() == "split":
            return {
                "DaysUntilTransfer": {
                    "type": str,
                    "required": False,
                    "description": "Days (0-93) funds are held before transfer; 0 = immediate",
                },
                **self._SPLIT_GROUPS,
            }

        if action.lower() in ("transfer", "refundsupplementary"):
            return dict(self._SPLIT_GROUPS)

        if action.lower() == "manualtransfer":
            return {
                "FromAccountId": {
                    "type": str,
                    "required": True,
                    "description": "Merchant GUID of the debited account (A)",
                },
                "ToAccountId": {
                    "type": str,
                    "required": True,
                    "description": "Merchant GUID of the credited account (B)",
                },
                "FromDescription": {
                    "type": str,
                    "required": True,
                    "description": "Description of the debit transaction in account A",
                },
                "ToDescription": {
                    "type": str,
                    "required": True,
                    "description": "Description of the credit transaction in account B",
                },
            }

        return {}

    def split(self, split: Dict[str, Any], validate: bool = True) -> CombinableService:
        """Build a Split service to combine into a payment.

        Combine the result into the funding payment, e.g.
        ``payments.create_payment("ideal", {...}).combine(mp).pay()``.

        Args:
            split: Spec dict with ``daysUntilTransfer`` (0-93; "0" = immediate,
                omit to hold until a later Transfer), ``marketplace`` and
                ``sellers`` groups.
            validate: Whether to validate and filter service parameters.
        """
        self._apply_split(split)
        service = self.build("Split", validate=validate).services.services[0]
        return CombinableService(services=[service])

    def refund_supplementary(
        self, split: Optional[Dict[str, Any]] = None, validate: bool = True
    ) -> CombinableService:
        """Build a RefundSupplementary service to combine into a refund.

        Combine the result into the consumer refund, e.g.
        ``payments.create_payment("ideal", {...}).combine(mp).refund()``. With no
        spec it reverts all transfers; pass ``sellers``/``marketplace`` to
        retrieve specific amounts per account.

        Args:
            split: Optional spec dict with ``marketplace`` and ``sellers`` groups.
            validate: Whether to validate and filter service parameters.
        """
        self._apply_split(split or {})
        service = self.build("RefundSupplementary", validate=validate).services.services[0]
        return CombinableService(services=[service])

    def transfer(self, transfer: Dict[str, Any], validate: bool = True) -> PaymentResponse:
        """Transfer held funds of an existing split payment (standalone).

        Args:
            transfer: Spec dict with ``originalTransactionKey`` (required) and,
                optionally, ``marketplace``/``sellers`` to re-specify the split
                (partial transfer). ``DaysUntilTransfer`` does not apply.
            validate: Whether to validate and filter service parameters.

        Raises:
            ValueError: If ``originalTransactionKey`` is missing.
        """
        original_transaction_key = transfer.get("originalTransactionKey")
        if not original_transaction_key:
            raise ValueError("Transfer requires an originalTransactionKey")

        self._apply_split(transfer)
        request_data = self.build("Transfer", validate=validate).to_dict()
        request_data["OriginalTransactionKey"] = original_transaction_key
        request_data.pop("AmountDebit", None)

        return self._post_data_request(request_data)

    def manual_transfer(
        self, manual_transfer: Dict[str, Any], validate: bool = True
    ) -> PaymentResponse:
        """Move funds directly between two accounts (standalone).

        Args:
            manual_transfer: Spec dict with ``fromAccountId``, ``toAccountId``,
                ``fromDescription``, ``toDescription``, ``amount`` and
                ``currency`` (all required), and optional ``invoice``.
            validate: Whether to validate and filter service parameters.

        Raises:
            ValueError: If a required field is missing.
        """
        fields = {
            "FromAccountId": manual_transfer.get("fromAccountId"),
            "ToAccountId": manual_transfer.get("toAccountId"),
            "FromDescription": manual_transfer.get("fromDescription"),
            "ToDescription": manual_transfer.get("toDescription"),
        }
        missing = [name for name, value in fields.items() if not value]
        if manual_transfer.get("amount") is None:
            missing.append("amount")
        currency = manual_transfer.get("currency") or self._currency
        if not currency:
            missing.append("currency")
        if missing:
            raise ValueError(f"ManualTransfer requires: {', '.join(missing)}")

        for name, value in fields.items():
            self.add_parameter(name, value)

        request_data = self.build("ManualTransfer", validate=validate).to_dict()
        request_data["Currency"] = currency
        request_data["Amount"] = manual_transfer["amount"]
        request_data.pop("AmountDebit", None)

        invoice = manual_transfer.get("invoice") or self._invoice
        if invoice:
            request_data["Invoice"] = invoice
        else:
            request_data.pop("Invoice", None)

        return self._post_data_request(request_data)

    def _apply_split(self, split: Dict[str, Any]) -> None:
        """Map a split spec dict into grouped Marketplaces service parameters."""
        days_until_transfer = split.get("daysUntilTransfer")
        if days_until_transfer is not None:
            self.add_parameter("DaysUntilTransfer", days_until_transfer)

        marketplace = split.get("marketplace")
        if marketplace:
            for name, value in marketplace.items():
                self.add_parameter(name, value, "Marketplace")

        for index, seller in enumerate(split.get("sellers") or [], start=1):
            for name, value in seller.items():
                self.add_parameter(name, value, "Seller", str(index))
