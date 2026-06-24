import graphene
import graphene.relay
from graphene_django.types import DjangoObjectType

from apibase.schema import NodeMixin, NodeSet

from .. import models
from ..models.methods import all_permissions
from . import filters


class User(NodeMixin, DjangoObjectType):
    permissions = graphene.List(graphene.String)

    class Meta:
        model = models.User
        filterset_class = filters.UserFilter
        interfaces = (graphene.Node,)
        convert_choices_to_enum = False
        exclude = ["password"]

    def resolve_permissions(root, info):
        return all_permissions(root)


class Group(NodeMixin, DjangoObjectType):
    class Meta:
        model = models.Group
        filterset_class = filters.GroupFilter
        interfaces = (graphene.Node,)
        convert_choices_to_enum = False
        exclude = []


class Permission(NodeMixin, DjangoObjectType):
    class Meta:
        model = models.Permission
        filterset_class = filters.PermissionFilter
        interfaces = (graphene.Node,)
        convert_choices_to_enum = False
        exclude = []


class ContentType(NodeMixin, DjangoObjectType):
    class Meta:
        model = models.ContentType
        filterset_class = filters.ContentTypeFilter
        interfaces = (graphene.Node,)
        convert_choices_to_enum = False
        exclude = []


class UserQueryMixin:
    user = graphene.relay.Node.Field(User)
    user_set = NodeSet(User)


class GroupQueryMixin:
    group = graphene.relay.Node.Field(Group)
    group_set = NodeSet(Group)


class PermissionQueryMixin:
    permission = graphene.relay.Node.Field(Permission)
    permission_set = NodeSet(Permission)


class ConteTypeQueryMixin:
    contenttype = graphene.relay.Node.Field(ContentType)
    contenttype_set = NodeSet(ContentType)


class Query(
    graphene.ObjectType,
    UserQueryMixin,
    GroupQueryMixin,
    PermissionQueryMixin,
    ConteTypeQueryMixin,
):
    pass
