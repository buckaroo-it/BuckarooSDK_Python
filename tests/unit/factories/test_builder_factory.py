import pytest

from buckaroo.factories.builder_factory import BuilderFactory


ABSTRACT_METHODS = (
    "create_builder",
    "register_method",
    "get_available_methods",
    "is_method_supported",
    "detect_method_from_payload",
)


def test_cannot_instantiate_abstract_base():
    with pytest.raises(TypeError):
        BuilderFactory()


def test_declares_expected_abstract_methods():
    assert BuilderFactory.__abstractmethods__ == frozenset(ABSTRACT_METHODS)


@pytest.mark.parametrize("name", ABSTRACT_METHODS)
def test_method_is_abstract_classmethod(name):
    attr = BuilderFactory.__dict__[name]
    assert isinstance(attr, classmethod), f"{name} must be a classmethod"
    assert getattr(attr.__func__, "__isabstractmethod__", False), (
        f"{name} must be marked @abstractmethod"
    )


# super() delegation on every override intentional: it executes the ABC's
# `pass` bodies, keeping them covered without pragmas.
class _FullFactory(BuilderFactory):
    _registry = {}

    @classmethod
    def create_builder(cls, method, client):
        super().create_builder(method, client)
        return ("builder", method, client)

    @classmethod
    def register_method(cls, method, builder_class):
        super().register_method(method, builder_class)
        cls._registry[method] = builder_class

    @classmethod
    def get_available_methods(cls):
        super().get_available_methods()
        return list(cls._registry)

    @classmethod
    def is_method_supported(cls, method):
        super().is_method_supported(method)
        return method in cls._registry

    @classmethod
    def detect_method_from_payload(cls, payload):
        super().detect_method_from_payload(payload)
        return payload["method"]


def test_concrete_subclass_instantiates_and_methods_callable():
    factory = _FullFactory()
    assert isinstance(factory, BuilderFactory)

    _FullFactory.register_method("ideal", object)
    assert _FullFactory.is_method_supported("ideal") is True
    assert _FullFactory.is_method_supported("missing") is False
    assert _FullFactory.get_available_methods() == ["ideal"]
    assert _FullFactory.create_builder("ideal", "client-sentinel") == (
        "builder",
        "ideal",
        "client-sentinel",
    )
    assert _FullFactory.detect_method_from_payload({"method": "ideal"}) == "ideal"


@pytest.mark.parametrize("missing", ABSTRACT_METHODS)
def test_partial_subclass_missing_one_method_raises(missing):
    attrs = {
        name: classmethod(lambda cls, *a, **kw: None)
        for name in ABSTRACT_METHODS
        if name != missing
    }
    Partial = type("Partial", (BuilderFactory,), attrs)

    with pytest.raises(TypeError) as excinfo:
        Partial()
    assert missing in str(excinfo.value)
