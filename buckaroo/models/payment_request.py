from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class Parameter:
    """Model for a service parameter."""
    name: str
    value: str
    group_type: str = ""
    group_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "Name": self.name,
            "GroupType": self.group_type,
            "GroupID": self.group_id,
            "Value": self.value
        }


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

    def add_parameter(self, parameter: Union[Dict[str, Any], Parameter]) -> "Service":
        """Append a Parameter or coerced dict; rejects dict-form parameters."""
        if isinstance(self.parameters, dict):
            raise TypeError(
                "Service uses simple key-value parameters; "
                "add_parameter requires list form"
            )
        if isinstance(parameter, dict):
            parameter = Parameter(
                name=parameter.get("Name", parameter.get("name", "")),
                value=parameter.get("Value", parameter.get("value", "")),
                group_type=parameter.get(
                    "GroupType", parameter.get("group_type", "")
                ),
                group_id=parameter.get(
                    "GroupID", parameter.get("group_id", "")
                ),
            )
        if self.parameters is None:
            self.parameters = []
        self.parameters.append(parameter)
        return self


@dataclass
class ServiceList:
    """Model for list of services."""
    services: List[Service]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "ServiceList": [service.to_dict() for service in self.services]
        }

    def add(self, service: Service) -> "ServiceList":
        """Append a service; returns self for chaining."""
        self.services.append(service)
        return self


@dataclass
class PaymentRequest:
    """Model for complete payment request."""
    currency: str
    amount_debit: float
    description: str
    invoice: str
    return_url: str
    return_url_cancel: str
    return_url_error: str
    return_url_reject: str
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
        request_dict = {
            "Currency": self.currency,
            "AmountDebit": self.amount_debit,
            "Description": self.description,
            "Invoice": self.invoice,
            "ReturnURL": self.return_url,
            "ReturnURLCancel": self.return_url_cancel,
            "ReturnURLError": self.return_url_error,
            "ReturnURLReject": self.return_url_reject,
            "ContinueOnIncomplete": self.continue_on_incomplete,
        }

        if self.push_url:
            request_dict["PushURL"] = self.push_url
        if self.push_url_failure:
            request_dict["PushURLFailure"] = self.push_url_failure

        if self.client_ip:
            request_dict["ClientIP"] = self.client_ip.to_dict()
            
        if self.services:
            request_dict["Services"] = self.services.to_dict()
            
        return request_dict