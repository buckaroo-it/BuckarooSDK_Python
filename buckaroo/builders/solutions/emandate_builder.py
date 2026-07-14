from typing import Dict, Any
from .solution_builder import SolutionBuilder


class EmandateBuilder(SolutionBuilder):
    """Builder for eMandate solutions (DataRequest-based mandate management)."""

    def get_service_name(self) -> str:
        """Get the service name for eMandate."""
        return "emandate"

    def get_allowed_service_parameters(self, action: str = "GetIssuerList") -> Dict[str, Any]:
        """Get the allowed service parameters for eMandate based on action."""

        if action.lower() in ["getissuerlist"]:
            return {}

        if action.lower() in ["createmandate"]:
            return {
                "debtorBankId": {
                    "type": str,
                    "required": False,
                    "description": "BIC of the debtor's bank",
                },
                "debtorReference": {
                    "type": str,
                    "required": True,
                    "description": "Debtor's reference for the mandate",
                },
                "sequenceType": {
                    "type": str,
                    "required": False,
                    "description": "Sequence type of the mandate (0 = one-off, 1 = recurring)",
                },
                "purchaseId": {
                    "type": str,
                    "required": False,
                    "description": "Unique purchase identifier",
                },
                "language": {
                    "type": str,
                    "required": False,
                    "description": "Language for the mandate flow",
                },
                "emandateReason": {
                    "type": str,
                    "required": False,
                    "description": "Reason for the mandate",
                },
                "maxAmount": {
                    "type": str,
                    "required": False,
                    "description": "Maximum amount allowed under the mandate",
                },
            }

        if action.lower() in ["getstatus"]:
            return {
                "mandateId": {
                    "type": str,
                    "required": True,
                    "description": "Identifier of the mandate to look up",
                },
            }

        if action.lower() in ["modifymandate"]:
            return {
                "mandateId": {
                    "type": str,
                    "required": True,
                    "description": "Identifier of the mandate to modify",
                },
                "maxAmount": {
                    "type": str,
                    "required": False,
                    "description": "Maximum amount allowed under the mandate",
                },
                "language": {
                    "type": str,
                    "required": False,
                    "description": "Language for the mandate flow",
                },
                "emandateReason": {
                    "type": str,
                    "required": False,
                    "description": "Reason for the mandate",
                },
            }

        if action.lower() in ["cancelmandate"]:
            return {
                "mandateId": {
                    "type": str,
                    "required": True,
                    "description": "Identifier of the mandate to cancel",
                },
                "purchaseId": {
                    "type": str,
                    "required": False,
                    "description": "Unique purchase identifier",
                },
            }

        return {}

    def issuer_list(self, validate: bool = True) -> Any:
        """Retrieve the list of available eMandate issuers via GetIssuerList."""
        payload = self.build("GetIssuerList", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def create_mandate(self, validate: bool = True) -> Any:
        """Create a mandate via CreateMandate.

        Requires ``debtorReference`` to be set (via ``add_parameter`` or the
        ``service_parameters`` payload key); the other Mandate parameters are
        optional. Raises :class:`RequiredParameterMissingError` when
        ``debtorReference`` is missing and ``validate`` is True.
        """
        payload = self.build("CreateMandate", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def status(self, validate: bool = True) -> Any:
        """Retrieve the status of a mandate via GetStatus.

        Requires ``mandateId`` to be set (via ``add_parameter`` or the
        ``service_parameters`` payload key). Raises
        :class:`RequiredParameterMissingError` when ``mandateId`` is missing
        and ``validate`` is True.
        """
        payload = self.build("GetStatus", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def modify_mandate(self, validate: bool = True) -> Any:
        """Modify a mandate via ModifyMandate.

        Requires ``mandateId`` to be set (via ``add_parameter`` or the
        ``service_parameters`` payload key); ``maxAmount``, ``language`` and
        ``emandateReason`` are optional. Raises
        :class:`RequiredParameterMissingError` when ``mandateId`` is missing
        and ``validate`` is True.
        """
        payload = self.build("ModifyMandate", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)

    def cancel_mandate(self, validate: bool = True) -> Any:
        """Cancel a mandate via CancelMandate.

        Requires ``mandateId`` to be set (via ``add_parameter`` or the
        ``service_parameters`` payload key); ``purchaseId`` is optional.
        Raises :class:`RequiredParameterMissingError` when ``mandateId`` is
        missing and ``validate`` is True.
        """
        payload = self.build("CancelMandate", validate=validate)
        request_data = payload.to_dict()

        return self._post_data_request(request_data)


class EmandateB2BBuilder(EmandateBuilder):
    """Builder for the Business (B2B) eMandate variant.

    Inherits every action and parameter spec from :class:`EmandateBuilder`
    unchanged; only the service name differs.
    """

    def get_service_name(self) -> str:
        """Get the service name for the B2B eMandate variant."""
        return "emandateb2b"
