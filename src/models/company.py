from .model_mixin import ModelMixin


class BankAccount(ModelMixin):
    _company_name: str
    _vat_applicable: bool
    _vat_number: str
    _chamber_of_commerce: str
