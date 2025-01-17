from typing import Self

from .payload import Payload
from ..additional_parameters import AdditionalParameters


class DataRequestPayload(Payload):
    def set_properties(self, data=None) -> Self:
        if "additionalParameters" in (data or {}):
            self.additional_parameters = AdditionalParameters(
                data["additionalParameters"], True
            )
            del data["additionalParameters"]

        super().set_properties(data)
        return self
