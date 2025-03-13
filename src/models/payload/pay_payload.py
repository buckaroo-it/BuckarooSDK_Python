import uuid

import src.models.payload.payload as payload


class PayPayload(payload.Payload):
    _order: str

    def __init__(self, values=dict):
        self._order = f"ORDER_NO_{uuid.uuid4().hex}"
        super().__init__(values)
