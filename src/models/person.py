import src.models.model_mixin as model_mixin
import src.models.recipient_interface as recipient_interface


class Person(model_mixin.ModelMixin, recipient_interface.RecipientInterface):
    _category: str
    _gender: str
    _culture: str
    _care_of: str
    _title: str
    _initials: str = ""
    _name: str
    _first_name: str
    _last_name_prefix: str
    _last_name: str
    _birth_date: str = ""
    _place_of_birth: str
