from typing import Optional, Union

from src.config import DefaultConfig, ConfigInterface
from src.payment_methods import payable_method_factory, PayableMethodInterface
from src.config import ConfigInterface
from src.transaction import Client
from typing import Type


class BuckarooClient:
    _config: ConfigInterface
    _client: Client

    def __init__(
        self, website_key: str | ConfigInterface, secret_key: str, mode: Optional[str]
    ):
        self._config = self.generate_config(website_key, secret_key, mode)
        self._client = Client(self._config)

    @property
    def config(self) -> ConfigInterface:
        return self._config

    @config.setter
    def config(self, config: ConfigInterface) -> None:
        self._config = config

    @property
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, client: Client) -> None:
        self._client = client

    def payable(self, payment_method: str) -> PayableMethodInterface:
        return payable_method_factory(payment_method, self.client)

    # @todo: Implement authorizable(payment_method: string): AuthorizableMethodBuilderInterface
    def authorizable(self, payment_method: str):
        # @todo: Add the implementation for authorizable method
        pass

    # @todo: Implement verifiable(payment_method: string): VerifiableMethodBuilderInterface
    def verifiable(self, payment_method: str):
        # @todo: Add the implementation for verifiable method
        pass

    # @todo: Implement encrypted_payable(payment_method: string): EncryptableMethodBuilderInterface
    def encrypted_payable(self, payment_method: str):
        # @todo: Add the implementation for encrypted_payable method
        pass

    # @todo: Implement payable_with_redirect(payment_method: string): RedirectPaymentMethodBuilderInterface
    def payable_with_redirect(self, payment_method: str):
        # @todo: Add the implementation for payable_with_redirect method
        pass

    # @todo: Implement payable_with_emandates(payment_method: string): EmandatesPaymentMethodBuilderInterface
    def payable_with_emandates(self, payment_method: str):
        # @todo: Add the implementation for payable_with_emandates method
        pass

    # @todo: Implement payable_with_one_click(payment_method: string): OneClickPaymentMethodBuilderInterface
    def payable_with_one_click(self, payment_method: str):
        # @todo: Add the implementation for payable_with_one_click method
        pass

    # @todo: Implement complete_encrypted_payable(payment_method: string): CompleteEncryptedPaymentMethodBuilderInterface
    def complete_encrypted_payable(self, payment_method: str):
        # @todo: Add the implementation for complete_encrypted_payable method
        pass

    # @todo: Implement voucher(payment_method: string): VoucherBuilderInterface
    def voucher(self, payment_method: str):
        # @todo: Add the implementation for voucher method
        pass

    # @todo: Implement wallet(payment_method: string): BuckarooWalletBuilderInterface
    def wallet(self, payment_method: str):
        # @todo: Add the implementation for wallet method
        pass

    # @todo: Implement credit_management(payment_method: string): CreditManagementBuilderInterface
    def credit_management(self, payment_method: str):
        # @todo: Add the implementation for credit_management method
        pass

    # @todo: Implement emandates(payment_method: string): EmandatesBuilderInterface
    def emandates(self, payment_method: str):
        # @todo: Add the implementation for emandates method
        pass

    # @todo: Implement fast_checkout(payment_method: string): FastCheckoutBuilderInterface
    def fast_checkout(self, payment_method: str):
        # @todo: Add the implementation for fast_checkout method
        pass

    # @todo: Implement qr(payment_method: string): QRBuilderInterface
    def qr(self, payment_method: str):
        # @todo: Add the implementation for qr method
        pass

    # @todo: Implement reserve(payment_method: string): ReserveBuilderInterface
    def reserve(self, payment_method: str):
        # @todo: Add the implementation for reserve method
        pass

    # @todo: Implement market_place(payment_method: string): MarketplaceBuilderInterface
    def market_place(self, payment_method: str):
        # @todo: Add the implementation for market_place method
        pass

    # @todo: Implement extra_info(payment_method: string): ExtraInfoBuilderInterface
    def extra_info(self, payment_method: str):
        # @todo: Add the implementation for extra_info method
        pass

    # @todo: Implement subscriptions(payment_method: string): SubscriptionsBuilderInterface
    def subscriptions(self, payment_method: str):
        # @todo: Add the implementation for subscriptions method
        pass

    # @todo: Implement get_active_subscriptions(): list
    def get_active_subscriptions(self):
        # @todo: Add the implementation for get_active_subscriptions method
        pass

    # @todo: Implement batch(transactions: list): BatchTransactions
    def batch(self, transactions: list):
        # @todo: Add the implementation for batch method
        pass

    # @todo: Implement transaction(transaction_key: str): TransactionService
    def transaction(self, transaction_key: str):
        # @todo: Add the implementation for transaction method
        pass

    # @todo: Implement attachLogger(logger: Observer): self
    def attachLogger(self, logger):
        # @todo: Add the implementation for attachLogger method
        pass

    def generate_config(
        self, website_key: str | ConfigInterface, secret_key: str, mode: Optional[str]
    ) -> ConfigInterface:
        if isinstance(website_key, ConfigInterface):
            return website_key
        else:
            return DefaultConfig(website_key, secret_key, mode)
