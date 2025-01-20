from __future__ import annotations

from ..payable_method_mixin import PayableMethodMixin
from src.transaction import Client


class Ideal(PayableMethodMixin):

    def __init__(self, client: Client):
        _payment_name = "ideal"
        _required_config_fields = [
            "currency",
            "returnURL",
            "returnURLCancel",
            "pushURL",
        ]
        _client = client
