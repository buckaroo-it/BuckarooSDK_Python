from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class Parameter:
    """Model for a service parameter (used for both requests and responses)."""
    name: str
    value: str
    group_type: Optional[str] = None
    group_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "Name": self.name,
            "GroupType": self.group_type or "",
            "GroupID": self.group_id or "",
            "Value": self.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Parameter':
        """Create Parameter from API response dictionary."""
        if data is None:
            data = {}
        value = data.get('Value')
        return cls(
            name=data.get('Name', ''),
            value=str(value) if value is not None else '',
            group_type=data.get('GroupType') or None,
            group_id=data.get('GroupID') or None,
        )


@dataclass
class ClientIP:
    """Model for client IP information."""
    type: int = 0
    address: str = "0.0.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "Type": self.type,
            "Address": self.address
        }


@dataclass
class Service:
    """Model for a payment service."""
    name: str
    action: str = "Pay"
    parameters: Optional[Union[Dict[str, Any], List[Parameter]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        service_dict = {
            "Name": self.name,
            "Action": self.action
        }
        
        if self.parameters:
            if isinstance(self.parameters, list):
                # Parameters array format (for methods like IdealQr)
                service_dict["Parameters"] = [param.to_dict() for param in self.parameters]
            elif isinstance(self.parameters, dict):
                # Simple key-value format (for methods like ideal, creditcard)
                service_dict.update(self.parameters)
                
        return service_dict


@dataclass
class ServiceList:
    """Model for list of services."""
    services: List[Service]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "ServiceList": [service.to_dict() for service in self.services]
        }


@dataclass
class PaymentRequest:
    """Model for complete payment request."""
    currency: Optional[str] = None
    amount_debit: Optional[float] = None
    description: Optional[str] = None
    invoice: Optional[str] = None
    return_url: Optional[str] = None
    return_url_cancel: Optional[str] = None
    return_url_error: Optional[str] = None
    return_url_reject: Optional[str] = None
    continue_on_incomplete: str = "1"
    push_url: Optional[str] = None
    push_url_failure: Optional[str] = None
    client_ip: Optional[ClientIP] = None
    services: Optional[ServiceList] = None

    def __post_init__(self):
        """Set default values after initialization."""
        if self.client_ip is None:
            self.client_ip = ClientIP()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        request_dict: Dict[str, Any] = {
            "ContinueOnIncomplete": self.continue_on_incomplete,
        }

        if self.currency is not None:
            request_dict["Currency"] = self.currency
        if self.amount_debit is not None:
            request_dict["AmountDebit"] = self.amount_debit
        if self.description is not None:
            request_dict["Description"] = self.description
        if self.invoice is not None:
            request_dict["Invoice"] = self.invoice
        if self.return_url is not None:
            request_dict["ReturnURL"] = self.return_url
        if self.return_url_cancel is not None:
            request_dict["ReturnURLCancel"] = self.return_url_cancel
        if self.return_url_error is not None:
            request_dict["ReturnURLError"] = self.return_url_error
        if self.return_url_reject is not None:
            request_dict["ReturnURLReject"] = self.return_url_reject
        if self.push_url:
            request_dict["PushURL"] = self.push_url
        if self.push_url_failure:
            request_dict["PushURLFailure"] = self.push_url_failure
        if self.client_ip:
            request_dict["ClientIP"] = self.client_ip.to_dict()
        if self.services:
            request_dict["Services"] = self.services.to_dict()

        return request_dict