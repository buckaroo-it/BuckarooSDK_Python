from typing import Any, Dict, Optional, Self

import src.services.service_list_parameters.service_list_parameter_interface as service_list_parameter_interface
import src.services.service_list_parameters.default_parameters as default_parameters
import src.services.service_list_parameters.model_parameters as model_parameters
import src.models.service_parameter_interface as service_parameter_interface
import src.models.model_interface as model_interface
import src.models.service_list_interface as service_list_interface


class ServiceList(service_list_interface.ServiceListInterface):
    def __init__(
        self,
        name: str,
        version: int,
        action: str,
        model: Optional[model_interface.ModelInterface] = None,
    ):
        self._name: str = name
        self._version: int = version
        self._action: str = action
        self._parameters: Dict[str, Any] = {}
        self._parameter_service: (
            service_list_parameter_interface.ServiceListParameterInterface
        ) = default_parameters.DefaultParameters(self)

        if model:
            self._decorate_parameters(model)
            self._parameter_service.data()

    def get_parameters(self) -> Dict[str, Any]:
        return self._parameters

    def append_parameter(self, value: Any, key: Optional[str] = None) -> Self:
        if isinstance(value, list) and all(isinstance(v, list) for v in value):
            for single_value in value:
                self.append_parameter(single_value, key)
            return self

        if key:
            self._parameters[key] = value

        return self

    def _decorate_parameters(
        self,
        model: model_interface.ModelInterface,
        group_type: Optional[str] = None,
        group_key: Optional[int] = None,
    ) -> Self:
        self._parameter_service = model_parameters.ModelParameters(
            self._parameter_service, model, group_type, group_key
        )
        self._iterate_through_object(model, model.get_object_vars())
        return self

    def _iterate_through_object(
        self,
        model: model_interface.ModelInterface,
        array: Dict[str, Any],
        key_name: Optional[str] = None,
    ) -> Self:
        for key, value in array.items():
            if isinstance(
                model, service_parameter_interface.ServiceParameterInterface
            ) and isinstance(value, model_interface.ModelInterface):
                self._decorate_parameters(
                    value,
                    model.get_group_type(key_name or key),
                    model.get_group_key(key_name or key),
                )
                continue

            if isinstance(value, list) and value:
                formatted_data = {str(index): item for index, item in enumerate(value)}
                self._iterate_through_object(model, formatted_data, key)

        return self
