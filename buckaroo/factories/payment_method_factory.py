from typing import Dict, Type, Any
from ..builders.payment_builder import PaymentBuilder
from ..builders.ideal_builder import IdealBuilder

class PaymentMethodFactory:
    """Factory for creating payment method builders."""
    
    # Registry of available payment methods
    _payment_methods: Dict[str, Type[PaymentBuilder]] = {
        "ideal": IdealBuilder
    }
    
    @classmethod
    def create_payment_builder(cls, method: str, client) -> PaymentBuilder:
        """
        Create a payment builder for the specified method.
        
        Args:
            method (str): The payment method name (e.g., 'ideal', 'creditcard', 'paypal')
            client: The Buckaroo client instance
            
        Returns:
            PaymentBuilder: A builder instance for the specified payment method
            
        Raises:
            ValueError: If the payment method is not supported
        """
        method = method.lower()
        
        if method not in cls._payment_methods:
            available_methods = ", ".join(cls._payment_methods.keys())
            raise ValueError(
                f"Unsupported payment method: {method}. "
                f"Available methods: {available_methods}"
            )
        
        builder_class = cls._payment_methods[method]
        return builder_class(client)
    
    @classmethod
    def register_payment_method(cls, method: str, builder_class: Type[PaymentBuilder]) -> None:
        """
        Register a new payment method builder.
        
        Args:
            method (str): The payment method name
            builder_class (Type[PaymentBuilder]): The builder class for this method
        """
        cls._payment_methods[method.lower()] = builder_class
    
    @classmethod
    def get_available_methods(cls) -> list:
        """
        Get a list of all available payment methods.
        
        Returns:
            list: List of available payment method names
        """
        return list(cls._payment_methods.keys())
    
    @classmethod
    def is_method_supported(cls, method: str) -> bool:
        """
        Check if a payment method is supported.
        
        Args:
            method (str): The payment method name
            
        Returns:
            bool: True if the method is supported, False otherwise
        """
        return method.lower() in cls._payment_methods
    
    @classmethod
    def detect_payment_method_from_payload(cls, payload: Dict) -> str:
        """
        Detect the payment method from payload parameters.
        
        Args:
            payload (Dict): Payment parameters dictionary
            
        Returns:
            str: Detected payment method name
            
        Raises:
            ValueError: If payment method cannot be determined from payload
        """
        # Check for explicit payment method in payload
        if 'payment_method' in payload:
            return payload['payment_method'].lower()
        if 'method' in payload:
            return payload['method'].lower()
        if 'service' in payload:
            return payload['service'].lower()
            
        # Auto-detect based on specific parameters
        
        # iDEAL indicators
        if 'issuer' in payload:
            return 'ideal'
            
        # Credit card indicators
        credit_card_fields = {'card_number', 'cardNumber', 'expiry_month', 'expiryMonth', 
                             'expiry_year', 'expiryYear', 'cvv', 'cardholder_name', 'cardholderName'}
        if any(field in payload for field in credit_card_fields):
            return 'creditcard'
            
        # Apple Pay indicators
        apple_pay_fields = {'payment_data', 'paymentData', 'apple_pay_token', 'applePayToken'}
        if any(field in payload for field in apple_pay_fields):
            return 'applepay'
            
        # PayPal indicators (typically no special fields, but could be explicit)
        if any(key.lower().startswith('paypal') for key in payload.keys()):
            return 'paypal'
            
        # iDEAL QR indicators
        if 'qr' in str(payload).lower() or 'idealqr' in str(payload).lower():
            return 'idealqr'
            
        # Default fallback - could be configurable
        raise ValueError(
            "Cannot determine payment method from payload. "
            "Please include 'payment_method', 'method', or 'service' field, "
            "or use method-specific parameters like 'issuer' for iDEAL, "
            "'card_number' for credit cards, etc."
        )
    
    @classmethod
    def detect_operation_from_payload(cls, payload: Dict) -> str:
        """
        Detect the operation type from payload parameters.
        
        Args:
            payload (Dict): Payment parameters dictionary
            
        Returns:
            str: Detected operation type ('pay', 'refund', 'capture', 'cancel')
        """
        # Check for explicit operation in payload
        if 'operation' in payload:
            return payload['operation'].lower()
        if 'action' in payload:
            return payload['action'].lower()
            
        # Auto-detect based on specific parameters
        
        # Refund indicators
        if 'original_transaction_key' in payload or 'refund_amount' in payload:
            return 'refund'
            
        # Capture indicators  
        if 'authorization_key' in payload or 'capture_amount' in payload:
            return 'capture'
            
        # Cancel indicators
        if 'cancel_key' in payload or payload.get('operation_type') == 'cancel':
            return 'cancel'
            
        # Default to payment
        return 'pay'