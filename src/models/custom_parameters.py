from typing import List, Optional, Self

import src.models.model_mixin as model_mixin


class CustomParameters(model_mixin.ModelMixin):
    def __init__(self, values: Optional[dict] = None):
        self._List: List[dict] = []
        self.set_properties(values)

    def set_properties(self, data: Optional[dict] = None) -> Self:
        for name, value in (data or {}).items():
            self._List.append({"Value": value, "Name": name})

        super().set_properties(data)
        return self
