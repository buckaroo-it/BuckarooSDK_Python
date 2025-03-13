import src.models.model_mixin as model_mixin


class BankAccount(model_mixin.ModelMixin):
    _iban: str
    _account_name: str
    _bic: str
