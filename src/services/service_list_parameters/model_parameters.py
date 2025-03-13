from typing import Optional

import src.models.model_interface as model_interface
import src.models.service_parameter_interface as service_parameter_interface
import src.services.service_list_parameters.service_list_parameter_interface as service_list_parameter_interface
import src.services.service_list_parameters.service_list_parameter_mixin as service_list_parameter_mixin
import src.models.service_list_interface as service_list_interface


class ModelParameters(service_list_parameter_mixin.ServiceListParameterMixin):
    def __init__(
        self,
        service_list_parameter: service_list_parameter_interface.ServiceListParameterInterface,
        model: model_interface.ModelInterface,
        group_type: Optional[str] = "",
        group_key: Optional[int] = None,
    ):
        self._model = model
        self._group_type = group_type
        self._group_key = group_key
        self._service_list_parameter = service_list_parameter
        self._service_list = self._service_list_parameter.data()

    @property
    def service_list(self) -> service_list_interface.ServiceListInterface:
        return self._service_list

    @property
    def model(self) -> model_interface.ModelInterface:
        return self._model

    def data(self):
        for key, value in self.model.to_dict().items():
            if not isinstance(value, list):
                self._append_parameter(
                    self.__group_key(key),
                    self.__group_type(key),
                    self.model.service_parameter_key_of(key),
                    value,
                )
        return self.service_list

    def __group_key(self, key):
        if (
            isinstance(
                self.model, service_parameter_interface.ServiceParameterInterface
            )
            and not self._group_key
        ):
            return self.model.get_group_key(key)
        return self._group_key

    def __group_type(self, key):
        if (
            isinstance(
                self.model,
                service_list_parameter_interface.ServiceListParameterInterface,
            )
            and not self._group_type
        ):
            return self.model.get_group_type(key)
        return self._group_type
