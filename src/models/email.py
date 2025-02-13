from .model_mixin import ModelMixin


class BankAccount(ModelMixin):
    _email: str

    def __init__(self):
        self.set_properties({"email": self._email})
