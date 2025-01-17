from typing import Self

from src.transaction import Client
from src.payment_methods import PayableMethodBuilderInterface
from .payable_method_builder_interface import PayableMethodBuilderInterface
from .payment_method_mixin import PaymentMethodMixin


class PayableMethodMixin(PayableMethodBuilderInterface, PaymentMethodMixin):
    _client: Client

    @property
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, client: Client) -> None:
        self._client = client

    def pay(self, data: dict) -> Self:
        return self

    def refund(self, data: dict) -> Self:
        return self

    def pay_remainder(self, data: dict) -> Self:
        return self
