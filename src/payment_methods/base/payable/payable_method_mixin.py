from typing import Self

from .payable_method_interface import PayableMethodInterface
from ..has_properties import HasClient


class PayableMethodMixin(PayableMethodInterface, HasClient):
    def pay(self, data: dict) -> Self:
        return self

    def refund(self, data: dict) -> Self:
        return self

    def pay_remainder(self, data: dict) -> Self:
        return self
