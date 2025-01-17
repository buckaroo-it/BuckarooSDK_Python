from typing import Optional, Dict

from ..model_mixin import ModelMixin
from ..client_ip import ClientIP
from ..additional_parameters import AdditionalParameters
from ..custom_parameters import CustomParameters


class Payload(ModelMixin):
    def __init__(self, values: Optional[Dict] = None):
        self.clientIP: Optional[ClientIP] = None
        self.currency: str = ""
        self.returnURL: str = ""
        self.returnURLError: str = ""
        self.returnURLCancel: str = ""
        self.returnURLReject: str = ""
        self.pushURL: str = ""
        self.pushURLFailure: str = ""
        self.invoice: str = ""
        self.description: str = ""
        self.originalTransactionKey: str = ""
        self.originalTransactionReference: str = ""
        self.websiteKey: str = ""
        self.culture: str = ""
        self.startRecurrent: bool = False
        self.continueOnIncomplete: str = ""
        self.servicesSelectableByClient: str = ""
        self.servicesExcludedForClient: str = ""
        self.additionalParameters: Optional[AdditionalParameters] = None
        self.customParameters: Optional[CustomParameters] = None

        self.set_properties(values)

    def set_properties(self, data: Optional[Dict] = None) -> "Payload":
        if data is None:
            return self

        if "customParameters" in data:
            self.customParameters = CustomParameters(data["customParameters"])
            del data["customParameters"]

        if "additionalParameters" in data:
            self.additionalParameters = AdditionalParameters(
                data["additionalParameters"]
            )
            del data["additionalParameters"]

        if "clientIP" in data:
            client_ip_data = data["clientIP"]
            self.clientIP = ClientIP(
                ip=client_ip_data.get("address"),
                ip_type=client_ip_data.get("type"),
            )
            del data["clientIP"]

        super().set_properties(data)
        return self
