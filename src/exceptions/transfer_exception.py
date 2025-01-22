from .buckaroo_exception import BuckarooException


class TransferException(BuckarooException):
    def __init__(self, message: str):
        super().__init__(f"Buckaroo TransferException {message}")
