from typing import Dict, Type, Any

from buckaroo.builders.payments.alipay_builder import AlipayBuilder
from buckaroo.builders.payments.creditcard_builder import CreditcardBuilder
from ..builders.payments.payment_builder import PaymentBuilder
from ..builders.payments.ideal_builder import IdealBuilder
from ..builders.payments.sofort_builder import SofortBuilder
from ..builders.payments.payconiq_builder import PayconiqBuilder

class PaymentMethodFactory:
    """Factory for creating payment method builders."""
    
    # Registry of available payment methods
    _payment_methods: Dict[str, Type[PaymentBuilder]] = {
        "alipay": AlipayBuilder,
        "ideal": IdealBuilder,
        "creditcard": CreditcardBuilder,
        "sofort": SofortBuilder,
        "payconiq": PayconiqBuilder,
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
        if 'method' in payload:
            return payload['method'].lower()
            
        # Default fallback - could be configurable
        raise ValueError(
            "Cannot determine payment method from payload. "
            "Please include 'method'."
        )