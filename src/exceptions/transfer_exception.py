import src.exceptions.buckaroo_exception as buckaroo_exception


class TransferException(buckaroo_exception.BuckarooException):
    def __init__(self, message: str):
        super().__init__(f"Buckaroo TransferException {message}")
