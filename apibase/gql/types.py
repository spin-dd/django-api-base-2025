from functools import reduce
from logging import getLogger

from graphene_django.types import DjangoObjectType as BaseObjectType

logger = getLogger()


def resolve_queryset(queryset, info, resolvers=None):
    if not resolvers:
        return queryset, info

    def _resolve(params, func):
        return func(*params)

    return reduce(_resolve, resolvers, (queryset, info))


class DjangoObjectType(BaseObjectType):
    @classmethod
    def get_queryset(cls, queryset, info):
        resolvers = getattr(cls, "queryset_resolvers", None)
        queryset, info = resolve_queryset(queryset, info, resolvers=resolvers)
        return queryset

    class Meta:
        abstract = True
