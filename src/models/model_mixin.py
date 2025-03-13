from typing import Any, Dict, Optional, Self

import src.models.model_interface as model_interface


class ModelMixin(model_interface.ModelInterface):
    def __getattr__(self, property_name: str) -> Any:
        if property_name in self.__dict__:
            return self.__dict__.get(property_name)
        return None

    def __setattr__(self, property_name: str, value: Any) -> None:
        self.__dict__[property_name.removeprefix("_")] = value

    def get_object_vars(self) -> Dict:
        return self.__dict__

    def set_properties(self, data: Optional[Dict] = None) -> Self:
        if data:
            for property_name, value in data.items():
                setattr(self, property_name, value)
        return self

    def service_parameter_key_of(self, property_name: str) -> str:
        cleaned_parameter = property_name.removeprefix("_")
        parameter_words = cleaned_parameter.split("_")
        return "".join(word.capitalize() for word in parameter_words)

    def to_dict(self) -> Dict:
        return self._recursive_to_dict(self.__dict__)

    def _recursive_to_dict(self, data: Dict) -> Dict:
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self._recursive_to_dict(value)
            else:
                result[key] = value
        return result
