from .model_mixin import ModelMixin


class BankAccount(ModelMixin):
    _iban: str
    _account_name: str
    _bic: str
