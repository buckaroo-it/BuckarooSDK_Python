from typing import Optional, Dict

import src.models.service_parameter_interface as service_parameter_interface
import src.models.model_mixin as model_mixin


class ServiceParameter(
    service_parameter_interface.ServiceParameterInterface, model_mixin.ModelMixin
):
    def set_properties(self, data: Optional[Dict] = None):
        if data is None:
            return self

        for property_name, value in data.items():
            method_name = f"set_{property_name}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                method(value)
            else:
                setattr(self, property_name, value)

        return self

    def get_group_type(self, key: str) -> Optional[str]:
        return self.group_data.get(key, {}).get("groupType", None)

    def get_group_key(self, key: str) -> Optional[int]:
        return self.group_data.get(key, {}).get("groupKey", None)
