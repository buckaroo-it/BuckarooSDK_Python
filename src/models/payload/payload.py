from typing import Optional, Dict, Self

import src.models.model_mixin as model_mixin
import src.models.client_ip as client_ip
import src.models.additional_parameters as additional_parameters
import src.models.custom_parameters as custom_parameters


class Payload(model_mixin.ModelMixin):
    def __init__(self, values: Optional[Dict] = None):
        self._client_ip: Optional[client_ip.ClientIP] = None
        self._currency: str = ""
        self._return_url: str = ""
        self._return_url_error: str = ""
        self._return_url_cancel: str = ""
        self._return_url_reject: str = ""
        self._push_url: str = ""
        self._push_url_failure: str = ""
        self._invoice: str = ""
        self._description: str = ""
        self._original_transaction_key: str = ""
        self._original_transaction_reference: str = ""
        self._website_key: str = ""
        self._culture: str = ""
        self._start_recurrent: bool = False
        self._continue_on_incomplete: str = ""
        self._services_selectable_by_client: str = ""
        self._services_excluded_for_client: str = ""
        self._additional_parameters: Optional[
            additional_parameters.AdditionalParameters
        ] = None
        self._custom_parameters: Optional[custom_parameters.CustomParameters] = None

        self.set_properties(values)

    def set_properties(self, data: Optional[Dict] = None) -> Self:
        if data is None:
            return self

        if "customParameters" in data:
            self._custom_parameters = custom_parameters.CustomParameters(
                data["customParameters"]
            )
            del data["customParameters"]

        if "additionalParameters" in data:
            self._additional_parameters = additional_parameters.AdditionalParameters(
                data["additionalParameters"]
            )
            del data["additionalParameters"]

        if "clientIP" in data:
            client_ip_data = data["clientIP"]
            self._client_ip = client_ip.ClientIP(
                ip=client_ip_data.get("address"),
                ip_type=client_ip_data.get("type"),
            )
            del data["clientIP"]

        super().set_properties(data)
        return self
