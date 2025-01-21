from .payable_method_interface import PayableMethodInterface
from src.transaction import Client
from ...ideal.ideal import Ideal

def payable_method_factory(payment_method: str, client: Client) -> PayableMethodInterface:
    if payment_method == "ideal":
        return Ideal(client)
    raise ValueError(f"Unknown payment method: {payment_method}")