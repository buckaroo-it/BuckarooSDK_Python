from typing import Any, Dict, Optional, Self

from .model_interface import ModelInterface
from src.services import ServiceListParameterInterface, DefaultParameters, ModelParameters
from .service_parameter_interface import ServiceParameterInterface

class ServiceList:
    def __init__(self, name: str, version: int, action: str, model: Optional[ModelInterface] = None):
        self.name: str = name
        self.version: int = version
        self.action: str = action
        self.parameters: Dict[str, Any] = {}
        self.parameter_service: ServiceListParameterInterface = DefaultParameters(self)

        if model:
            self.decorate_parameters(model)
            self.parameter_service.data()

    def get_parameters(self) -> Dict[str, Any]:
        return self.parameters

    def append_parameter(self, value: Any, key: Optional[str] = None) -> Self:
        if isinstance(value, list) and all(isinstance(v, list) for v in value):
            for single_value in value:
                self.append_parameter(single_value, key)
            return self

        if key:
            self.parameters[key] = value
        else:
            self.parameters[len(self.parameters)] = value
        
        return self

    def decorate_parameters(self, model: ModelInterface, group_type: Optional[str] = None, group_key: Optional[int] = None) -> Self:
        self.parameter_service = ModelParameters(self.parameter_service, model, group_type, group_key)
        self.iterate_through_object(model, model.get_object_vars())
        return self

    def iterate_through_object(self, model: ModelInterface, array: Dict[str, Any], key_name: Optional[str] = None) -> Self:
        for key, value in array.items():
            if isinstance(model, ServiceParameterInterface) and isinstance(value, ModelInterface):
                self.decorate_parameters(
                    value,
                    model.get_group_type(key_name or key),
                    model.get_group_key(key_name or key, key if isinstance(key, int) else None)
                )
                continue

            if isinstance(value, list) and len(value):
                self.iterate_through_object(model, {k: v for k, v in enumerate(value)}, key)

        return self
