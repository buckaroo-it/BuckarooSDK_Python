import src.resources.constants.response_status as response_status
import src.transaction.response.response as response


class TransactionResponse(response.Response):
    def is_success(self):
        return self.get_status_code() == response_status.BUCKAROO_STATUSCODE_SUCCESS

    def is_failed(self):
        return self.get_status_code() == response_status.BUCKAROO_STATUSCODE_FAILED

    def is_canceled(self):
        status_code = self.get_status_code()
        return status_code in [
            response_status.BUCKAROO_STATUSCODE_CANCELLED_BY_USER,
            response_status.BUCKAROO_STATUSCODE_CANCELLED_BY_MERCHANT,
        ]

    def is_awaiting_consumer(self):
        return (
            self.get_status_code()
            == response_status.BUCKAROO_STATUSCODE_WAITING_ON_CONSUMER
        )

    def is_pending_processing(self):
        return (
            self.get_status_code()
            == response_status.BUCKAROO_STATUSCODE_PENDING_PROCESSING
        )

    def is_waiting_on_user_input(self):
        return (
            self.get_status_code()
            == response_status.BUCKAROO_STATUSCODE_WAITING_ON_USER_INPUT
        )

    def is_rejected(self):
        return self.get_status_code() == response_status.BUCKAROO_STATUSCODE_REJECTED

    def is_pending_approval(self):
        return (
            self.get_status_code()
            == response_status.BUCKAROO_STATUSCODE_PENDING_APPROVAL
        )

    def is_validation_failure(self):
        return (
            self.get_status_code()
            == response_status.BUCKAROO_STATUSCODE_VALIDATION_FAILURE
        )

    def data(self, key=None):
        if key and key in self.data:
            return self.data[key]
        return self.data

    def has_redirect(self):
        return (
            "RequiredAction" in self.data
            and "RedirectURL" in self.data["RequiredAction"]
            and self.data["RequiredAction"]["Name"] == "Redirect"
        )

    def get_redirect_url(self):
        if self.has_redirect():
            return self.data["RequiredAction"]["RedirectURL"]
        return ""

    def get_method(self):
        return self.data["Services"][0]["Name"]

    def get_service_action(self):
        return self.data["Services"][0]["Action"]

    def get_service_parameters(self):
        params = {}
        if "Services" in self.data and "Parameters" in self.data["Services"][0]:
            for parameter in self.data["Services"][0]["Parameters"]:
                params[parameter["Name"].lower()] = parameter["Value"]
        return params

    def get_custom_parameters(self):
        params = {}
        if "CustomParameters" in self.data and "List" in self.data["CustomParameters"]:
            for parameter in self.data["CustomParameters"]["List"]:
                params[parameter["Name"]] = parameter["Value"]
        return params

    def get_additional_parameters(self):
        params = {}
        if (
            "AdditionalParameters" in self.data
            and "AdditionalParameter" in self.data["AdditionalParameters"]
        ):
            for parameter in self.data["AdditionalParameters"]["AdditionalParameter"]:
                params[parameter["Name"]] = parameter["Value"]
        return params

    def get_transaction_key(self):
        return self.data["Key"]

    def get_payment_key(self):
        return self.data["PaymentKey"]

    def get_token(self):
        params = self.get_additional_parameters()
        return params.get("token", "").strip()

    def get_signature(self):
        params = self.get_additional_parameters()
        return params.get("signature", "").strip()

    def get_amount(self):
        return str(self.data.get("AmountDebit", ""))

    def get_currency(self):
        return self.data.get("Currency", "")

    def get_invoice(self):
        return self.data.get("Invoice", "")

    def get_status_code(self):
        if (
            "Status" in self.data
            and "Code" in self.data["Status"]
            and "Code" in self.data["Status"]["Code"]
        ):
            return self.data["Status"]["Code"]["Code"]
        return None

    def get_sub_status_code(self):
        if (
            "Status" in self.data
            and "SubCode" in self.data["Status"]
            and "Code" in self.data["Status"]["SubCode"]
        ):
            return self.data["Status"]["SubCode"]["Code"]
        return None

    def has_some_error(self):
        return bool(self.get_some_error())

    def get_some_error(self):
        if self.has_error():
            error = self.get_first_error()
            return error["ErrorMessage"] if error else ""
        if self.has_consumer_message():
            return self.get_consumer_message()
        if self.has_message():
            return self.get_message()
        if self.has_sub_code_message():
            return self.get_sub_code_message()
        return ""

    def has_error(self):
        return any(
            [
                "RequestErrors" in self.data,
                "ChannelErrors" in self.data["RequestErrors"],
                "ServiceErrors" in self.data["RequestErrors"],
                "ActionErrors" in self.data["RequestErrors"],
                "ParameterErrors" in self.data["RequestErrors"],
                "CustomParameterErrors" in self.data["RequestErrors"],
            ]
        )

    def get_first_error(self):
        error_types = [
            "ChannelErrors",
            "ServiceErrors",
            "ActionErrors",
            "ParameterErrors",
            "CustomParameterErrors",
        ]
        if self.has_error():
            for error_type in error_types:
                if (
                    error_type in self.data["RequestErrors"]
                    and self.data["RequestErrors"][error_type]
                ):
                    return self.data["RequestErrors"][error_type][0]
        return {}

    def has_message(self):
        return "Message" in self.data and bool(self.data["Message"])

    def get_message(self):
        return self.data.get("Message", "")

    def has_consumer_message(self):
        return (
            "ConsumerMessage" in self.data
            and "HtmlText" in self.data["ConsumerMessage"]
        )

    def get_consumer_message(self):
        return (
            self.data["ConsumerMessage"]["HtmlText"]
            if self.has_consumer_message()
            else ""
        )

    def has_sub_code_message(self):
        return (
            "Status" in self.data
            and "SubCode" in self.data["Status"]
            and "Description" in self.data["Status"]["SubCode"]
        )

    def get_sub_code_message(self):
        return (
            self.data["Status"]["SubCode"]["Description"]
            if self.has_sub_code_message()
            else ""
        )

    def get_customer_name(self):
        return self.data.get("CustomerName", "")

    def get(self, key):
        return self.data.get(key)
