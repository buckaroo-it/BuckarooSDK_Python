from abc import ABC, abstractmethod
from typing import Self

from .payment_method_builder_interface import PaymentMethodBuilderInterface


class PayableMethodBuilderInterface(PaymentMethodBuilderInterface, ABC):

    @abstractmethod
    def pay(self, data: dict) -> Self:
        pass

    @abstractmethod
    def refund(self, data: dict) -> Self:
        pass

    @abstractmethod
    def pay_remainder(self, data: dict) -> Self:
        pass
