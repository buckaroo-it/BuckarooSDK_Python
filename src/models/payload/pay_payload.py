import uuid

from .payload import Payload


class PayPayload(Payload):
    def __init__(self, values=dict):
        self.order = f"ORDER_NO_{uuid.uuid4().hex}"
        super().__init__(values)
