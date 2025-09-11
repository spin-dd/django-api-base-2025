import rest_framework
from django.http import HttpResponse
from graphene_django import settings, views

try:  # graphql-core v3
    from graphql.utilities import print_schema
except Exception:  # fallback for graphql-core v2
    from graphql.utils import schema_printer

    def print_schema(schema):  # type: ignore
        return schema_printer.print_schema(schema)


from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings


def _decorate(view):
    view = permission_classes((IsAuthenticated,))(view)
    view = authentication_classes(api_settings.DEFAULT_AUTHENTICATION_CLASSES)(view)
    return api_view(["GET", "POST"])(view)


class DRFAuthenticatedGraphQLView(views.GraphQLView):
    def parse_body(self, request):
        if isinstance(request, rest_framework.request.Request):
            return request.data
        return super().parse_body(request)

    @classmethod
    def as_view(cls, *args, **kwargs):
        return _decorate(super().as_view(*args, **kwargs))


@_decorate
def sdl(request):
    """GraphQL Schema Definition Language (SDL)."""
    schema_obj = settings.graphene_settings.SCHEMA
    gql_schema = getattr(schema_obj, "graphql_schema", None) or getattr(schema_obj, "schema", None) or schema_obj
    schema_str = print_schema(gql_schema)
    return HttpResponse(schema_str, content_type="text/plain")
