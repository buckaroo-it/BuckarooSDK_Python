import src.services.service_list_parameters.service_list_parameter_mixin as service_list_parameter_mixin
import src.models.service_list_interface as service_list_interface


class DefaultParameters(service_list_parameter_mixin.ServiceListParameterMixin):
    def __init__(self, new_service_list: service_list_interface.ServiceListInterface):
        self._service_list = new_service_list

    @property
    def service_list(self) -> service_list_interface.ServiceListInterface:
        return self._service_list
