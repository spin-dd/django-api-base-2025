import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from apibase.schema import BaseSerializerMutation, NodeMixin, NodeSet, default_resolver

from .filters import BookFilter
from .models import Book
from .serializers import BookSerializer


class BookNode(NodeMixin, DjangoObjectType):
    class Meta:
        model = Book
        interfaces = (relay.Node,)
        fields = ("id", "title", "author", "published", "created_at")
        default_resolver = default_resolver


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    # EPM style naming: {model}_set
    book_set = NodeSet(BookNode, filterset_class=BookFilter)


class UpsertBook(BaseSerializerMutation):
    class Meta:
        serializer_class = BookSerializer


class Mutation(graphene.ObjectType):
    upsert_book = UpsertBook.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
