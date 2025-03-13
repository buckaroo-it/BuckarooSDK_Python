from abc import ABC, abstractmethod
from typing import Any, Optional

import src.services.service_list_parameters.service_list_parameter_interface as service_list_parameter_interface
import src.models.service_list as service_list


class ServiceListParameterMixin(
    service_list_parameter_interface.ServiceListParameterInterface, ABC
):

    @property
    @abstractmethod
    def service_list(self) -> "service_list.ServiceList":
        pass

    def data(self):
        return self.service_list

    def _append_parameter(
        self, group_key: Optional[int], group_type: Optional[str], name: str, value: Any
    ) -> service_list_parameter_interface.ServiceListParameterInterface:
        if value is not None:
            self.service_list.append_parameter(
                {
                    "Name": name,
                    "Value": value,
                    "GroupType": "" if group_type is None else group_type,
                    "GroupID": "" if group_key is None else group_key,
                }
            )

        return self
