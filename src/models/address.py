import src.models.model_mixin as model_mixin


class Address(model_mixin.ModelMixin):
    _street: str
    _house_number: str
    _house_number_additional: str
    _zip_code: str
    _city: str
    _state: str
    _country: str
