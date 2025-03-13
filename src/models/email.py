import src.models.model_mixin as model_mixin


class BankAccount(model_mixin.ModelMixin):
    _email: str

    def __init__(self):
        self.set_properties({"email": self._email})
