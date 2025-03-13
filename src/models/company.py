import src.models.model_mixin as model_mixin


class BankAccount(model_mixin.ModelMixin):
    _company_name: str
    _vat_applicable: bool
    _vat_number: str
    _chamber_of_commerce: str
