from typing import Self, Protocol

from ..has_properties import HasClient


class PayableMethodInterface(Protocol, HasClient):
    def pay(self, data: dict) -> Self:
        return self

    def refund(self, data: dict) -> Self:
        return self

    def pay_remainder(self, data: dict) -> Self:
        return self
