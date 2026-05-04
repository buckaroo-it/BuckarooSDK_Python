"""
Payment Response Model for Buckaroo SDK.

This module provides response objects for payment transactions.
"""

from typing import Any, Dict, Iterator, List, Optional
from dataclasses import dataclass
from enum import IntEnum


class BuckarooStatusCode(IntEnum):
    """Canonical Buckaroo transaction status codes."""

    SUCCESS = 190
    FAILED = 490
    VALIDATION_FAILURE = 491
    TECHNICAL_FAILURE = 492
    REJECTED = 690
    REJECTED_BY_USER = 691
    REJECTED_TECHNICAL = 692
    PENDING_INPUT = 790
    PENDING_PROCESSING = 791
    PENDING_CONSUMER = 792
    AWAITING_TRANSFER = 793
    CANCELLED_BY_USER = 890
    CANCELLED_BY_MERCHANT = 891


_PENDING_CODES = frozenset(
    {
        BuckarooStatusCode.PENDING_INPUT,
        BuckarooStatusCode.PENDING_PROCESSING,
        BuckarooStatusCode.PENDING_CONSUMER,
        BuckarooStatusCode.AWAITING_TRANSFER,
    }
)
_CANCELLED_CODES = frozenset(
    {
        BuckarooStatusCode.CANCELLED_BY_USER,
        BuckarooStatusCode.CANCELLED_BY_MERCHANT,
    }
)
_FAILED_CODES = frozenset(
    {
        BuckarooStatusCode.FAILED,
        BuckarooStatusCode.VALIDATION_FAILURE,
        BuckarooStatusCode.TECHNICAL_FAILURE,
        BuckarooStatusCode.REJECTED,
        BuckarooStatusCode.REJECTED_BY_USER,
        BuckarooStatusCode.REJECTED_TECHNICAL,
    }
)


@dataclass
class StatusCode:
    """Represents a Buckaroo status code."""

    code: int
    description: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusCode":
        """Create StatusCode from dictionary."""
        if data is None:
            data = {}

        # Handle nested Code structure: {"Code": 490, "Description": "Failed"}
        if isinstance(data, dict) and "Code" in data and "Description" in data:
            return cls(code=data.get("Code", 0), description=data.get("Description", ""))
        # Handle simple structure: {"Code": 490} or just integer
        elif isinstance(data, dict):
            return cls(code=data.get("Code", 0), description=data.get("Description", ""))
        # Handle direct integer
        elif isinstance(data, int):
            return cls(code=data, description="")
        else:
            return cls(code=0, description="")


@dataclass
class Status:
    """Represents the status of a payment transaction."""

    code: StatusCode
    sub_code: StatusCode
    datetime: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Status":
        """Create Status from dictionary."""
        if data is None:
            data = {}

        # Handle SubCode being None
        sub_code_data = data.get("SubCode")
        if sub_code_data is None:
            sub_code_data = {}

        return cls(
            code=StatusCode.from_dict(data.get("Code", {})),
            sub_code=StatusCode.from_dict(sub_code_data),
            datetime=data.get("DateTime", ""),
        )


@dataclass
class RequiredAction:
    """Represents a required action for the payment."""

    redirect_url: Optional[str]
    requested_information: Optional[Any]
    pay_remainder_details: Optional[Any]
    name: str
    type_deprecated: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequiredAction":
        """Create RequiredAction from dictionary."""
        if data is None:
            data = {}
        return cls(
            redirect_url=data.get("RedirectURL"),
            requested_information=data.get("RequestedInformation"),
            pay_remainder_details=data.get("PayRemainderDetails"),
            name=data.get("Name", ""),
            type_deprecated=data.get("TypeDeprecated", 0),
        )


@dataclass
class ServiceParameter:
    """Represents a service parameter."""

    name: str
    value: Any

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceParameter":
        """Create ServiceParameter from dictionary."""
        if data is None:
            data = {}
        return cls(name=data.get("Name", ""), value=data.get("Value"))


@dataclass
class Service:
    """Represents a payment service."""

    name: str
    action: Optional[str]
    parameters: List[ServiceParameter]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Service":
        """Create Service from dictionary."""
        if data is None:
            data = {}

        parameters = []
        if "Parameters" in data and data["Parameters"]:
            parameters = [ServiceParameter.from_dict(param) for param in data["Parameters"]]

        return cls(name=data.get("Name", ""), action=data.get("Action"), parameters=parameters)


class PaymentResponse:
    """
    Represents a response from the Buckaroo payment API.

    This class provides convenient access to all payment response data
    and includes helper methods for common operations.
    """

    def __init__(self, response_data: Dict[str, Any]):
        """
        Initialize PaymentResponse from response dictionary.

        Args:
            response_data: Raw response data from BuckarooResponse.to_dict()
        """
        if response_data is None:
            response_data = {}
        self._raw_data = response_data
        self._parse_response()

    def _parse_response(self):
        """Parse the response data into structured objects."""
        data = self._raw_data.get("data", {})

        # Basic response info
        self.status_code = self._raw_data.get("status_code", 0)
        self.success = self._raw_data.get("success", False)
        self.headers = self._raw_data.get("headers", {})

        # Payment identifiers
        self.key = data.get("Key")
        self.payment_key = data.get("PaymentKey")

        # Status information
        self.status = Status.from_dict(data.get("Status", {})) if "Status" in data else None

        # Required action (for redirects, etc.)
        required_action_data = data.get("RequiredAction")
        self.required_action = (
            RequiredAction.from_dict(required_action_data)
            if required_action_data is not None
            else None
        )

        # Services
        self.services = []
        if "Services" in data and data["Services"]:
            self.services = [Service.from_dict(service) for service in data["Services"]]

        # Payment details
        self.invoice = data.get("Invoice")
        self.service_code = data.get("ServiceCode")
        self.is_test = data.get("IsTest", False)
        self.currency = data.get("Currency")
        self.amount_debit = data.get("AmountDebit")
        self.amount_credit = data.get("AmountCredit")  # For refunds
        self.transaction_type = data.get("TransactionType")
        self.mutation_type = data.get("MutationType")

        # Additional fields
        self.custom_parameters = data.get("CustomParameters")
        self.additional_parameters = data.get("AdditionalParameters")
        self.request_errors = data.get("RequestErrors")
        self.related_transactions = data.get("RelatedTransactions")
        self.consumer_message = data.get("ConsumerMessage")
        self.message = data.get("Message")
        self.order = data.get("Order")
        self.issuing_country = data.get("IssuingCountry")
        self.start_recurrent = data.get("StartRecurrent", False)
        self.recurring = data.get("Recurring", False)
        self.customer_name = data.get("CustomerName")
        self.payer_hash = data.get("PayerHash")

        # Convenience properties from BuckarooResponse
        self.is_successful_payment = self._raw_data.get("is_successful_payment", False)
        self.transaction_key = self._raw_data.get("transaction_key")
        self.buckaroo_status_code = self._raw_data.get("buckaroo_status_code")
        self.buckaroo_status_message = self._raw_data.get("buckaroo_status_message")
        self.redirect_url = self._raw_data.get("redirect_url")

    def is_pending(self) -> bool:
        """Check if the payment is pending."""
        if self.status and self.status.code:
            return self.status.code.code in _PENDING_CODES
        return False

    def is_successful(self) -> bool:
        """Check if the payment was successful."""
        return self.is_successful_payment

    def is_cancelled(self) -> bool:
        """Check if the payment was cancelled."""
        if self.status and self.status.code:
            return self.status.code.code in _CANCELLED_CODES
        return False

    def is_failed(self) -> bool:
        """Check if the payment failed."""
        if self.status and self.status.code:
            return self.status.code.code in _FAILED_CODES
        return False

    def requires_action(self) -> bool:
        """Check if the payment requires additional action (like redirect)."""
        return self.required_action is not None

    def get_redirect_url(self) -> Optional[str]:
        """Get the redirect URL from the required action, if any."""
        if self.required_action is not None:
            return self.required_action.redirect_url
        return self.redirect_url

    def get_transaction_id(self) -> Optional[str]:
        """Get the transaction ID from service parameters."""
        for service in self.services:
            for param in service.parameters:
                if param.name.lower() == "transactionid":
                    return param.value
        return None

    def get_service_parameter(self, parameter_name: str) -> Optional[Any]:
        """
        Get a specific service parameter value.

        Args:
            parameter_name: Name of the parameter to retrieve

        Returns:
            Parameter value if found, None otherwise
        """
        for service in self.services:
            for param in service.parameters:
                if param.name.lower() == parameter_name.lower():
                    return param.value
        return None

    _ERROR_TYPES = (
        "ChannelErrors",
        "ServiceErrors",
        "ActionErrors",
        "ParameterErrors",
        "CustomParameterErrors",
    )

    @staticmethod
    def _normalize_error_bucket(bucket: Any) -> List[Dict[str, Any]]:
        """Coerce a ``RequestErrors`` bucket into a list of dict entries.

        Real-world Buckaroo responses occasionally collapse a single-error
        bucket into a bare dict, or supply unexpected scalars. Coerce both
        shapes here so callers can iterate without type checks.
        """
        if isinstance(bucket, list):
            return [entry for entry in bucket if isinstance(entry, dict)]
        if isinstance(bucket, dict):
            return [bucket]
        return []

    def _iter_error_entries(self) -> Iterator[Dict[str, Any]]:
        """Yield error-entry dicts across every bucket in priority order."""
        errors = self.request_errors
        if not isinstance(errors, dict):
            return
        for bucket_name in self._ERROR_TYPES:
            for entry in self._normalize_error_bucket(errors.get(bucket_name)):
                yield entry

    def has_error(self) -> bool:
        """Return True when ``RequestErrors`` carries any usable entry."""
        return next(self._iter_error_entries(), None) is not None

    def get_first_error(self) -> Dict[str, Any]:
        """Return the first error entry from ``RequestErrors``, or ``{}``."""
        return next(self._iter_error_entries(), {})

    def has_consumer_message(self) -> bool:
        """Return True when the response carries a non-empty ConsumerMessage."""
        message = self.consumer_message or {}
        if isinstance(message, dict):
            return bool(message.get("HtmlText"))
        return False

    def get_consumer_message(self) -> str:
        """Return the consumer-facing HTML message, or ``''``."""
        message = self.consumer_message or {}
        if isinstance(message, dict):
            return message.get("HtmlText") or ""
        return ""

    def has_message(self) -> bool:
        """Return True when the top-level ``Message`` field is set."""
        return bool(self.message)

    def get_message(self) -> str:
        """Return the top-level ``Message`` field, or ``''``."""
        return self.message or ""

    def has_sub_code_message(self) -> bool:
        """Return True when ``Status.SubCode.Description`` is set."""
        return bool(
            self.status
            and self.status.sub_code
            and self.status.sub_code.description
        )

    def get_sub_code_message(self) -> str:
        """Return the ``Status.SubCode.Description``, or ``''``."""
        if self.has_sub_code_message():
            return self.status.sub_code.description
        return ""

    def has_some_error(self) -> bool:
        """Return True when any error/message channel carries text."""
        return bool(self.get_some_error())

    def get_some_error(self) -> str:
        """Return the most-specific error message from the response.

        Walks the response in priority order, mirroring PHP SDK's
        ``TransactionResponse::getSomeError``:

        1. The first entry from ``RequestErrors[*]`` (ChannelErrors,
           ServiceErrors, ActionErrors, ParameterErrors,
           CustomParameterErrors) → ``ErrorMessage``.
        2. ``ConsumerMessage.HtmlText`` (consumer-facing copy).
        3. Top-level ``Message`` (gateway-level message).
        4. ``Status.SubCode.Description`` (e.g. Riverty 491 reason).

        Returns ``''`` when none of those carry text.
        """
        for entry in self._iter_error_entries():
            message = entry.get("ErrorMessage")
            if message:
                return message
        if self.has_consumer_message():
            return self.get_consumer_message()
        if self.has_message():
            return self.get_message()
        if self.has_sub_code_message():
            return self.get_sub_code_message()
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response back to a dictionary."""
        return self._raw_data

    def __str__(self) -> str:
        """String representation of the payment response."""
        status_desc = (
            f"{self.status.code.code} - {self.status.code.description}"
            if self.status
            else "Unknown"
        )
        return f"PaymentResponse(key={self.key}, status={status_desc}, amount={self.amount_debit} {self.currency})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"PaymentResponse(key={self.key}, payment_key={self.payment_key}, "
            f"status_code={self.status_code}, success={self.success}, "
            f"is_test={self.is_test}, currency={self.currency}, "
            f"amount={self.amount_debit})"
        )
