from typing import Dict, Type, Any
import logging

from buckaroo.builders.payments.alipay_builder import AlipayBuilder
from buckaroo.builders.payments.apple_pay_builder import ApplePayBuilder
from buckaroo.builders.payments.bancontact_builder import BancontactBuilder
from buckaroo.builders.payments.belfius_builder import BelfiusBuilder
from buckaroo.builders.payments.bizum_builder import BizumBuilder
from buckaroo.builders.payments.blik_builder import BlikBuilder
from buckaroo.builders.payments.buckaroo_voucher_builder import BuckarooVoucherBuilder
from buckaroo.builders.payments.click_to_pay_builder import ClickToPayBuilder
from buckaroo.builders.payments.credit_card_builder import CreditcardBuilder
from buckaroo.builders.payments.default_builder import DefaultBuilder
from ..builders.payments.payment_builder import PaymentBuilder
from ..builders.payments.ideal_builder import IdealBuilder
from ..builders.payments.sofort_builder import SofortBuilder
from ..builders.payments.payconiq_builder import PayconiqBuilder

class PaymentMethodFactory:
    """Factory for creating payment method builders."""
    
    # Registry of available payment methods
    _payment_methods: Dict[str, Type[PaymentBuilder]] = {
        "alipay": AlipayBuilder,
        "applepay": ApplePayBuilder,
        "bancontact": BancontactBuilder,
        "bizum": BizumBuilder,
        "belfius": BelfiusBuilder,
        "blik": BlikBuilder,
        "buckaroovoucher": BuckarooVoucherBuilder,
        "credit_card": CreditcardBuilder,
        "clicktopay": ClickToPayBuilder,
        "default": DefaultBuilder,
        "ideal": IdealBuilder,
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
            logging.warning(
                f"Unsupported payment method: {method}. "
                f"Available methods: {available_methods}. "
                f"Using DefaultBuilder as fallback."
            )
            # Use DefaultBuilder as fallback
            return DefaultBuilder(client)
        
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
        
        # Check Services.ServiceList for payment method detection
        services = payload.get('Services', {})
        service_list = services.get('ServiceList', [])
        
        if service_list:
            for service in service_list:
                service_name = service.get('Name', '').lower()
                if service_name in cls._payment_methods:
                    return service_name
                
                # Map known service names to payment methods
                service_mapping = {
                    'alipay': 'alipay',
                    'applepay': 'applepay',
                    'ideal': 'ideal', 
                    'creditcard': 'creditcard',
                    'sofort': 'sofort',
                    'payconiq': 'payconiq'
                }
                
                if service_name in service_mapping:
                    return service_mapping[service_name]
            
        # Default fallback - could be configurable
        logging.warning(
            "Cannot determine payment method from payload. "
            "Please include 'method' or specify service in Services.ServiceList. "
            "Using 'default' as fallback method."
        )
        return 'default'