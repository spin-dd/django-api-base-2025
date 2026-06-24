import importlib
import sys
from types import ModuleType

APIBASE_SURFACE_MODULES = (
    "apibase._spectacular",
    "apibase.serializers",
    "apibase.viewsets",
)

DRF_SPECTACULAR_MODULES = (
    "drf_spectacular",
    "drf_spectacular.types",
    "drf_spectacular.utils",
)


class _BlockDrfSpectacular:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "drf_spectacular" or fullname.startswith("drf_spectacular."):
            raise ImportError("blocked drf-spectacular for import smoke")
        return None


def _drop_modules(monkeypatch, names):
    for name in names:
        monkeypatch.delitem(sys.modules, name, raising=False)


def _import_apibase_surface():
    spectacular = importlib.import_module("apibase._spectacular")
    serializers = importlib.import_module("apibase.serializers")
    viewsets = importlib.import_module("apibase.viewsets")
    return spectacular, serializers, viewsets


def _assert_union_surface(spectacular, serializers, viewsets):
    assert hasattr(spectacular.OpenApiTypes, "URI")
    assert hasattr(spectacular.OpenApiTypes, "STR")
    assert spectacular.OpenApiParameter.PATH == "path"
    assert callable(spectacular.extend_schema)
    assert callable(spectacular.extend_schema_field)

    assert serializers.OpenApiTypes is spectacular.OpenApiTypes
    assert serializers.extend_schema_field is spectacular.extend_schema_field
    assert viewsets.OpenApiTypes is spectacular.OpenApiTypes
    assert viewsets.OpenApiParameter is spectacular.OpenApiParameter
    assert viewsets.extend_schema is spectacular.extend_schema


def test_imports_without_drf_spectacular_expose_noop_union_surface(monkeypatch):
    _drop_modules(monkeypatch, APIBASE_SURFACE_MODULES)
    _drop_modules(monkeypatch, DRF_SPECTACULAR_MODULES)
    monkeypatch.setattr(sys, "meta_path", [_BlockDrfSpectacular(), *sys.meta_path])

    spectacular, serializers, viewsets = _import_apibase_surface()

    _assert_union_surface(spectacular, serializers, viewsets)

    class FieldTarget:
        pass

    def view_target():
        return None

    assert spectacular.extend_schema_field(spectacular.OpenApiTypes.URI)(FieldTarget) is FieldTarget
    assert spectacular.extend_schema()(view_target) is view_target


def test_imports_with_drf_spectacular_expose_real_union_surface(monkeypatch):
    _drop_modules(monkeypatch, APIBASE_SURFACE_MODULES)
    _drop_modules(monkeypatch, DRF_SPECTACULAR_MODULES)

    package = ModuleType("drf_spectacular")
    package.__path__ = []

    types_module = ModuleType("drf_spectacular.types")

    class FakeOpenApiTypes:
        URI = "fake-uri"
        STR = "fake-str"

    types_module.OpenApiTypes = FakeOpenApiTypes

    utils_module = ModuleType("drf_spectacular.utils")

    class FakeOpenApiParameter:
        PATH = "path"

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    def fake_extend_schema(*args, **kwargs):
        def decorator(target):
            return target

        return decorator

    def fake_extend_schema_field(*args, **kwargs):
        def decorator(target):
            return target

        return decorator

    utils_module.OpenApiParameter = FakeOpenApiParameter
    utils_module.extend_schema = fake_extend_schema
    utils_module.extend_schema_field = fake_extend_schema_field

    monkeypatch.setitem(sys.modules, "drf_spectacular", package)
    monkeypatch.setitem(sys.modules, "drf_spectacular.types", types_module)
    monkeypatch.setitem(sys.modules, "drf_spectacular.utils", utils_module)

    spectacular, serializers, viewsets = _import_apibase_surface()

    _assert_union_surface(spectacular, serializers, viewsets)
    assert spectacular.OpenApiTypes.URI == "fake-uri"
    assert spectacular.OpenApiTypes.STR == "fake-str"
