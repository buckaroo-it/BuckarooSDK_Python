from typing import List, Optional, Self

from .model_mixin import ModelMixin


class CustomParameters(ModelMixin):
    def __init__(self, values: Optional[dict] = None):
        self.List: List[dict] = []
        self.set_properties(values)

    def set_properties(self, data: Optional[dict] = None) -> Self:
        for name, value in (data or {}).items():
            self.List.append({"Value": value, "Name": name})

        super().set_properties(data)
        return self
