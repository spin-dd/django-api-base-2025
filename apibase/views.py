from django.http import HttpResponse

import rest_framework
from graphene_django import settings, views
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from graphql import print_schema


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


# Backward compatibility alias
DRFGraphQLView = DRFAuthenticatedGraphQLView


@_decorate
def sdl(request):
    """GraphQL Schema Definition Language (SDL)."""
    schema_obj = settings.graphene_settings.SCHEMA
    gql_schema = getattr(schema_obj, "graphql_schema", None) or getattr(schema_obj, "schema", None) or schema_obj
    schema_str = print_schema(gql_schema)
    return HttpResponse(schema_str, content_type="text/plain")
