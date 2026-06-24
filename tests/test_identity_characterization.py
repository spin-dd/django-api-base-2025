from types import SimpleNamespace

from apibase.graphql.mixins import NodeMixin
from apibase.serializers import BaseModelSerializer
from tests.models import Parent


class _ParentIdentitySerializer(BaseModelSerializer):
    class Meta:
        model = Parent
        fields = ["endpoint", "urn", "display"]


class _RequestBuilder:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def build_absolute_uri(self, path):
        return f"{self.base_url}{path}"


def _parent(pk=7):
    return Parent(id=pk, name="parent")


def _parent_with_endpoint(pk=7):
    parent = _parent(pk=pk)
    parent.get_endpoint_url = lambda: f"/parents/{parent.pk}/"
    return parent


def test_identity_module_exposes_transport_neutral_calculations():
    from apibase import identity

    parent = _parent_with_endpoint()

    assert identity.endpoint(parent) == "/parents/7/"
    assert identity.endpoint(_parent()) == ""
    assert identity.urn(parent) == "urn:x-nid:self:tests:parent:7"
    assert identity.display(parent) == "Parent object (7)"


def test_rest_identity_fields_preserve_relative_output_without_request():
    parent = _parent_with_endpoint()

    data = _ParentIdentitySerializer(parent).data

    assert data["endpoint"] == "/parents/7/"
    assert data["urn"] == "urn:x-nid:self:tests:parent:7"
    assert data["display"] == "Parent object (7)"


def test_rest_identity_endpoint_preserves_absolute_output_with_request():
    parent = _parent_with_endpoint()
    request = _RequestBuilder("https://api.example.test")

    data = _ParentIdentitySerializer(parent, context={"request": request}).data

    assert data["endpoint"] == "https://api.example.test/parents/7/"


def test_graphql_identity_resolvers_preserve_relative_and_absolute_outputs():
    parent = _parent_with_endpoint()

    relative_info = SimpleNamespace(context=object())
    absolute_info = SimpleNamespace(context=_RequestBuilder("https://api.example.test"))

    assert NodeMixin.resolve_endpoint(parent, relative_info) == "/parents/7/"
    assert NodeMixin.resolve_endpoint(parent, absolute_info) == "https://api.example.test/parents/7/"
    assert NodeMixin.resolve_urn(parent, relative_info) == "urn:x-nid:self:tests:parent:7"
    assert NodeMixin.resolve_display(parent, relative_info) == "Parent object (7)"


def test_endpoint_fallback_differs_between_rest_and_graphql_when_reverse_fails():
    parent = _parent()
    info = SimpleNamespace(context=object())

    assert _ParentIdentitySerializer(parent).data["endpoint"] is None
    assert NodeMixin.resolve_endpoint(parent, info) == ""
