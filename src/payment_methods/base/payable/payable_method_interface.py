from typing import Self
from abc import ABC, abstractmethod

import src.payment_methods.base.payment.payment_method_interface as payment_method_interface


class PayableMethodInterface(payment_method_interface.PaymentMethodInterface, ABC):

    @abstractmethod
    def pay(self, data: dict) -> Self:
        pass

    @abstractmethod
    def refund(self, data: dict) -> Self:
        pass

    @abstractmethod
    def pay_remainder(self, data: dict) -> Self:
        pass
