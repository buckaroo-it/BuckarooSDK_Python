"""
Payment Response Model for Buckaroo SDK.

This module provides response objects for payment transactions.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StatusCode:
    """Represents a Buckaroo status code."""
    code: int
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusCode':
        """Create StatusCode from dictionary."""
        return cls(
            code=data.get('Code', 0),
            description=data.get('Description', '')
        )


@dataclass
class Status:
    """Represents the status of a payment transaction."""
    code: StatusCode
    sub_code: StatusCode
    datetime: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Status':
        """Create Status from dictionary."""
        return cls(
            code=StatusCode.from_dict(data.get('Code', {})),
            sub_code=StatusCode.from_dict(data.get('SubCode', {})),
            datetime=data.get('DateTime', '')
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
    def from_dict(cls, data: Dict[str, Any]) -> 'RequiredAction':
        """Create RequiredAction from dictionary."""
        return cls(
            redirect_url=data.get('RedirectURL'),
            requested_information=data.get('RequestedInformation'),
            pay_remainder_details=data.get('PayRemainderDetails'),
            name=data.get('Name', ''),
            type_deprecated=data.get('TypeDeprecated', 0)
        )


@dataclass
class ServiceParameter:
    """Represents a service parameter."""
    name: str
    value: Any
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceParameter':
        """Create ServiceParameter from dictionary."""
        return cls(
            name=data.get('Name', ''),
            value=data.get('Value')
        )


@dataclass
class Service:
    """Represents a payment service."""
    name: str
    action: Optional[str]
    parameters: List[ServiceParameter]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Service':
        """Create Service from dictionary."""
        parameters = []
        if 'Parameters' in data and data['Parameters']:
            parameters = [ServiceParameter.from_dict(param) for param in data['Parameters']]
        
        return cls(
            name=data.get('Name', ''),
            action=data.get('Action'),
            parameters=parameters
        )


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
        self._raw_data = response_data
        self._parse_response()
    
    def _parse_response(self):
        """Parse the response data into structured objects."""
        data = self._raw_data.get('data', {})
        
        # Basic response info
        self.status_code = self._raw_data.get('status_code', 0)
        self.success = self._raw_data.get('success', False)
        self.headers = self._raw_data.get('headers', {})
        
        # Payment identifiers
        self.key = data.get('Key')
        self.payment_key = data.get('PaymentKey')
        
        # Status information
        self.status = Status.from_dict(data.get('Status', {})) if 'Status' in data else None
        
        # Required action (for redirects, etc.)
        self.required_action = RequiredAction.from_dict(data.get('RequiredAction', {})) if 'RequiredAction' in data else None
        
        # Services
        self.services = []
        if 'Services' in data and data['Services']:
            self.services = [Service.from_dict(service) for service in data['Services']]
        
        # Payment details
        self.invoice = data.get('Invoice')
        self.service_code = data.get('ServiceCode')
        self.is_test = data.get('IsTest', False)
        self.currency = data.get('Currency')
        self.amount_debit = data.get('AmountDebit')
        self.transaction_type = data.get('TransactionType')
        self.mutation_type = data.get('MutationType')
        
        # Additional fields
        self.custom_parameters = data.get('CustomParameters')
        self.additional_parameters = data.get('AdditionalParameters')
        self.request_errors = data.get('RequestErrors')
        self.related_transactions = data.get('RelatedTransactions')
        self.consumer_message = data.get('ConsumerMessage')
        self.order = data.get('Order')
        self.issuing_country = data.get('IssuingCountry')
        self.start_recurrent = data.get('StartRecurrent', False)
        self.recurring = data.get('Recurring', False)
        self.customer_name = data.get('CustomerName')
        self.payer_hash = data.get('PayerHash')
        
        # Convenience properties from BuckarooResponse
        self.is_successful_payment = self._raw_data.get('is_successful_payment', False)
        self.transaction_key = self._raw_data.get('transaction_key')
        self.buckaroo_status_code = self._raw_data.get('buckaroo_status_code')
        self.buckaroo_status_message = self._raw_data.get('buckaroo_status_message')
        self.redirect_url = self._raw_data.get('redirect_url')
    
    def is_pending(self) -> bool:
        """Check if the payment is pending."""
        if self.status and self.status.code:
            # Common pending status codes
            pending_codes = [790, 791, 792, 793]
            return self.status.code.code in pending_codes
        return False
    
    def is_successful(self) -> bool:
        """Check if the payment was successful."""
        return self.is_successful_payment
    
    def is_cancelled(self) -> bool:
        """Check if the payment was cancelled."""
        if self.status and self.status.code:
            # Common cancelled status codes
            cancelled_codes = [890, 891]
            return self.status.code.code in cancelled_codes
        return False
    
    def is_failed(self) -> bool:
        """Check if the payment failed."""
        if self.status and self.status.code:
            # Common failed status codes
            failed_codes = [490, 491, 492, 690, 691, 692]
            return self.status.code.code in failed_codes
        return False
    
    def requires_action(self) -> bool:
        """Check if the payment requires additional action (like redirect)."""
        return self.required_action is not None
    
    def get_redirect_url(self) -> Optional[str]:
        """Get the redirect URL if available."""
        return self.redirect_url
    
    def get_transaction_id(self) -> Optional[str]:
        """Get the transaction ID from service parameters."""
        for service in self.services:
            for param in service.parameters:
                if param.name.lower() == 'transactionid':
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the response back to a dictionary."""
        return self._raw_data
    
    def __str__(self) -> str:
        """String representation of the payment response."""
        status_desc = f"{self.status.code.code} - {self.status.code.description}" if self.status else "Unknown"
        return f"PaymentResponse(key={self.key}, status={status_desc}, amount={self.amount_debit} {self.currency})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"PaymentResponse(key={self.key}, payment_key={self.payment_key}, "
                f"status_code={self.status_code}, success={self.success}, "
                f"is_test={self.is_test}, currency={self.currency}, "
                f"amount={self.amount_debit})")