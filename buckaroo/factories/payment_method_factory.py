from typing import Dict, Type
from ..builders.payment_builder import PaymentBuilder
from ..builders.ideal_payment_builder import IdealPaymentBuilder
from ..builders.creditcard_payment_builder import CreditCardPaymentBuilder
from ..builders.paypal_payment_builder import PaypalPaymentBuilder
from ..builders.idealqr_payment_builder import IdealQrPaymentBuilder
from ..builders.applepay_payment_builder import ApplePayPaymentBuilder


class PaymentMethodFactory:
    """Factory for creating payment method builders."""
    
    # Registry of available payment methods
    _payment_methods: Dict[str, Type[PaymentBuilder]] = {
        "ideal": IdealPaymentBuilder,
        "creditcard": CreditCardPaymentBuilder,
        "paypal": PaypalPaymentBuilder,
        "idealqr": IdealQrPaymentBuilder,
        "applepay": ApplePayPaymentBuilder,
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