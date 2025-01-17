from src.exceptions import BuckarooException
from src.payment_methods import PayableMethodBuilderInterface
from src.payment_methods import Ideal
from src.transaction import Client


def payable_method_factory(
    payment_method: str, client: Client
) -> PayableMethodBuilderInterface:
    if payment_method == "ideal":
        return Ideal(client)
    else:
        raise BuckarooException("No such payment method exists")
