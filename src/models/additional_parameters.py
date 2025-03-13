from typing import List, Optional, Self

import src.models.model_mixin as model_mixin


class AdditionalParameters(model_mixin.ModelMixin):
    def __init__(self, values: Optional[dict] = None, is_data_request: bool = False):
        self.AdditionalParameter: Optional[List[dict]] = []
        self.List: Optional[List[dict]] = []
        self.is_data_request: bool = is_data_request

        self.set_properties(values)

    def set_properties(self, data: Optional[dict] = None) -> Self:
        for name, value in (data or {}).items():
            if self.is_data_request and self.List:
                self.List.append({"Value": value, "Name": name})
            else:
                if self.AdditionalParameter:
                    self.AdditionalParameter.append({"Value": value, "Name": name})

        super().set_properties(data)
        return self
