from typing import Dict, Type, Any
import logging

from .builder_factory import BuilderFactory
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
from buckaroo.builders.payments.eps_builder import EpsBuilder
from buckaroo.builders.payments.external_payment_builder import ExternalPaymentBuilder
from buckaroo.builders.payments.giftcards_builder import GiftcardsBuilder
from buckaroo.builders.payments.google_pay_builder import GooglePayBuilder
from buckaroo.builders.payments.ideal_qr_builder import IdealQrBuilder
from buckaroo.builders.payments.in3_builder import In3Builder
from buckaroo.builders.payments.kbc_builder import KBCBuilder
from buckaroo.builders.payments.billink_builder import BillinkBuilder
from buckaroo.builders.payments.klarna_builder import KlarnaBuilder
from buckaroo.builders.payments.klarnakp_builder import KlarnaKPBuilder
from buckaroo.builders.payments.knaken_builder import KnakenBuilder
from buckaroo.builders.payments.przelewy24_builder import Przelewy24Builder
from buckaroo.builders.payments.riverty_builder import RivertyBuilder
from buckaroo.builders.payments.sepadirectdebit_builder import SepaDirectDebitBuilder
from buckaroo.builders.payments.swish_builder import SwishBuilder
from buckaroo.builders.payments.transfer_builder import TransferBuilder
from buckaroo.builders.payments.trustly_builder import TrustlyBuilder
from buckaroo.builders.payments.twint_builder import TwintBuilder
from buckaroo.builders.payments.wechatpay_builder import WeChatPayBuilder
from buckaroo.builders.payments.wero_builder import WeroBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.ideal_builder import IdealBuilder
from buckaroo.builders.payments.sofort_builder import SofortBuilder
from buckaroo.builders.payments.payconiq_builder import PayconiqBuilder
from buckaroo.builders.payments.voucher_builder import VoucherBuilder
from buckaroo.builders.payments.multibanco_builder import MultibancoBuilder
from buckaroo.builders.payments.mbway_builder import MBWayBuilder
from buckaroo.builders.payments.paypal_builder import PaypalBuilder
from buckaroo.builders.payments.paybybank_builder import PayByBankBuilder

class PaymentMethodFactory(BuilderFactory):
    """Factory for creating payment method builders."""
    
    # Registry of available payment methods
    _payment_methods: Dict[str, Type[PaymentBuilder]] = {
        "alipay": AlipayBuilder,
        "applepay": ApplePayBuilder,
        "bancontact": BancontactBuilder,
        "belfius": BelfiusBuilder,
        "bizum": BizumBuilder,
        "billink": BillinkBuilder,
        "blik": BlikBuilder,
        "buckaroovoucher": BuckarooVoucherBuilder,
        "clicktopay": ClickToPayBuilder,
        "creditcard": CreditcardBuilder,
        "default": DefaultBuilder,
        "externalPayment": ExternalPaymentBuilder,
        "eps": EpsBuilder,
        "giftcards": GiftcardsBuilder,
        "googlepay": GooglePayBuilder,
        "ideal": IdealBuilder,
        "idealqr": IdealQrBuilder,
        "in3": In3Builder,
        "kbc": KBCBuilder,
        "knaken": KnakenBuilder,
        "klarna": KlarnaBuilder,
        "klarnakp": KlarnaKPBuilder,
        "multibanco": MultibancoBuilder,
        "mbway": MBWayBuilder,
        "payconiq": PayconiqBuilder,
        "paypal": PaypalBuilder,
        "paybybank": PayByBankBuilder,
        "przelewy24": Przelewy24Builder,
        "riverty": RivertyBuilder,
        "sepadirectdebit": SepaDirectDebitBuilder,
        "sofort": SofortBuilder,
        "swish": SwishBuilder,
        "transfer": TransferBuilder,
        "trustly": TrustlyBuilder,
        "twint": TwintBuilder,
        "voucher": VoucherBuilder,
        "wechatpay": WeChatPayBuilder,
        "wero": WeroBuilder,
    }
    
    @classmethod
    def create_builder(cls, method: str, client) -> PaymentBuilder:
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
    def register_method(cls, method: str, builder_class: Type[PaymentBuilder]) -> None:
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
    def detect_method_from_payload(cls, payload: Dict[str, Any]) -> str:
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
            
        # Default fallback - could be configurable
        logging.warning(
            "Cannot determine payment method from payload. "
            "Please include 'method' or specify service in Services.ServiceList. "
            "Using 'default' as fallback method."
        )
        return 'default'