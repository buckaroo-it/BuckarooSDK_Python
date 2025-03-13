from typing import Self

import src.models.additional_parameters as additional_parameters
import src.models.payload.payload as payload


class DataRequestPayload(payload.Payload):
    def set_properties(self, data=None) -> Self:
        if "additionalParameters" in (data or {}):
            self.additional_parameters = additional_parameters.AdditionalParameters(
                data["additionalParameters"], True
            )
            del data["additionalParameters"]

        super().set_properties(data)
        return self
