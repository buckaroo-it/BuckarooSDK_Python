from .model_mixin import ModelMixin


class Article(ModelMixin):
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
