from typing import Self
from abc import ABC, abstractmethod

from ..payment.payment_method_interface import PaymentMethodInterface


class PayableMethodInterface(PaymentMethodInterface, ABC):

    @abstractmethod
    def pay(self, data: dict) -> Self:
        pass

    @abstractmethod
    def refund(self, data: dict) -> Self:
        pass

    @abstractmethod
    def pay_remainder(self, data: dict) -> Self:
        pass
