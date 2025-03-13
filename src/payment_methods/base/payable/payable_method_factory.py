import src.transaction.client as client
import src.payment_methods.ideal.ideal as ideal
import src.payment_methods.base.payable.payable_method_interface as payable_method_interface


def payable_method_factory(
    payment_method: str, client: client.Client
) -> payable_method_interface.PayableMethodInterface:
    if payment_method == "ideal":
        return ideal.Ideal(client)
    raise ValueError(f"Unknown payment method: {payment_method}")
