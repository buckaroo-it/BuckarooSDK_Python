import src.models.model_mixin as model_mixin


class Article(model_mixin.ModelMixin):
    _identifier: str
    _type: str
    _brand: str
    _manufacturer: str
    _unit_code: str
    _price: float
    _quantity: int
    _vat_percentage: float
    _vat_category: str
    _description: str
