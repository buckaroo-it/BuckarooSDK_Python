from typing import Dict, Any, List
from datetime import datetime, date
from .payment_builder import PaymentBuilder
from ..models.payment_request import Parameter, PaymentRequest


class IdealQrPaymentBuilder(PaymentBuilder):
    """Builder for iDEAL QR payments."""
    
    def __init__(self, client):
        """Initialize IdealQr payment builder."""
        super().__init__(client)
        self._parameters: List[Parameter] = []
        
    def get_service_name(self) -> str:
        """Get the service name for iDEAL QR payments."""
        return "IdealQr"
    
    def get_action(self) -> str:
        """Get the action for iDEAL QR payments."""
        return "Generate"
    
    def add_qr_parameter(self, name: str, value: str, group_type: str = "", group_id: str = "") -> 'IdealQrPaymentBuilder':
        """Add a QR-specific parameter."""
        parameter = Parameter(name=name, value=value, group_type=group_type, group_id=group_id)
        self._parameters.append(parameter)
        return self
    
    def description(self, description: str) -> 'IdealQrPaymentBuilder':
        """Set the QR code description."""
        return self.add_qr_parameter("Description", description)
    
    def min_amount(self, amount: float) -> 'IdealQrPaymentBuilder':
        """Set the minimum amount for the QR payment."""
        return self.add_qr_parameter("MinAmount", str(amount))
    
    def max_amount(self, amount: float) -> 'IdealQrPaymentBuilder':
        """Set the maximum amount for the QR payment."""
        return self.add_qr_parameter("MaxAmount", str(amount))
    
    def image_size(self, size: int) -> 'IdealQrPaymentBuilder':
        """Set the QR code image size."""
        return self.add_qr_parameter("ImageSize", str(size))
    
    def purchase_id(self, purchase_id: str) -> 'IdealQrPaymentBuilder':
        """Set the purchase ID."""
        return self.add_qr_parameter("PurchaseId", purchase_id)
    
    def is_one_off(self, one_off: bool = True) -> 'IdealQrPaymentBuilder':
        """Set whether this is a one-off payment."""
        return self.add_qr_parameter("IsOneOff", str(one_off).lower())
    
    def amount(self, amount: float) -> 'IdealQrPaymentBuilder':
        """Set the amount for the QR payment."""
        # Override parent method to add as QR parameter
        super().amount(amount)  # Set for parent validation
        return self.add_qr_parameter("Amount", str(amount))
    
    def amount_is_changeable(self, changeable: bool = True) -> 'IdealQrPaymentBuilder':
        """Set whether the amount can be changed by the user."""
        return self.add_qr_parameter("AmountIsChangeable", str(changeable).lower())
    
    def expiration(self, expiration_date: str) -> 'IdealQrPaymentBuilder':
        """
        Set the expiration date for the QR code.
        
        Args:
            expiration_date: Date in format 'YYYY-MM-DD' or datetime/date object
        """
        if isinstance(expiration_date, (datetime, date)):
            expiration_date = expiration_date.strftime('%Y-%m-%d')
        return self.add_qr_parameter("Expiration", expiration_date)
    
    def is_processing(self, processing: bool = False) -> 'IdealQrPaymentBuilder':
        """Set whether the QR code is in processing state."""
        return self.add_qr_parameter("IsProcessing", str(processing).lower())
    
    def from_dict(self, data: Dict[str, Any]) -> 'IdealQrPaymentBuilder':
        """
        Populate the IdealQr builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            IdealQrPaymentBuilder: Self for method chaining
            
        Additional IdealQr-specific keys:
            - qr_description: QR code description (str)
            - min_amount: Minimum amount (float)
            - max_amount: Maximum amount (float)
            - image_size: QR image size (int)
            - purchase_id: Purchase identifier (str)
            - is_one_off: One-off payment flag (bool)
            - amount_is_changeable: Amount changeable flag (bool)
            - expiration: Expiration date (str in YYYY-MM-DD format)
            - is_processing: Processing state flag (bool)
        """
        # Handle QR-specific parameters
        if 'qr_description' in data:
            self.description(data['qr_description'])
        if 'min_amount' in data:
            self.min_amount(data['min_amount'])
        if 'max_amount' in data:
            self.max_amount(data['max_amount'])
        if 'image_size' in data:
            self.image_size(data['image_size'])
        if 'purchase_id' in data:
            self.purchase_id(data['purchase_id'])
        if 'is_one_off' in data:
            self.is_one_off(data['is_one_off'])
        if 'amount' in data:
            self.amount(data['amount'])
        if 'amount_is_changeable' in data:
            self.amount_is_changeable(data['amount_is_changeable'])
        if 'expiration' in data:
            self.expiration(data['expiration'])
        if 'is_processing' in data:
            self.is_processing(data['is_processing'])
            
        return self
    
    def _validate_required_fields(self) -> None:
        """Override validation since IdealQr has different requirements."""
        # IdealQr doesn't need all the standard payment fields
        # Only validate QR-specific required fields
        required_qr_params = ['Description', 'PurchaseId', 'Amount']
        existing_param_names = [param.name for param in self._parameters]
        
        missing_params = [param for param in required_qr_params if param not in existing_param_names]
        if missing_params:
            raise ValueError(f"Missing required QR parameters: {', '.join(missing_params)}")
    
    def build(self) -> PaymentRequest:
        """Build the IdealQr payment request."""
        self._validate_required_fields()
        
        # Create service with parameters array
        from ..models.payment_request import Service, ServiceList
        
        service = Service(
            name=self.get_service_name(),
            action=self.get_action(),
            parameters=self._parameters
        )
        
        # Create service list
        service_list = ServiceList(services=[service])
        
        # Build payment request - IdealQr doesn't use standard payment fields
        # We'll create a minimal request with just the Services
        payment_request = PaymentRequest(
            currency=self._currency or "EUR",  # Default currency
            amount_debit=self._amount_debit or 0.0,  # Will be overridden by QR amount
            description=self._description or "QR Payment",  # Default description
            invoice=self._invoice or "",  # Not required for QR
            return_url=self._return_url or "",  # Not required for QR
            return_url_cancel=self._return_url_cancel or "",
            return_url_error=self._return_url_error or "",
            return_url_reject=self._return_url_reject or "",
            continue_on_incomplete=self._continue_on_incomplete,
            client_ip=self._client_ip,
            services=service_list
        )
        
        return payment_request