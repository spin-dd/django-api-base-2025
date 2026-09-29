# GraphQL統合

apibaseは、Graphene-Djangoを拡張したGraphQL統合機能を提供します。

## 概要

apibaseのGraphQL機能:

- カスタムミックスイン
- 拡張フィールド
- コネクション（Relay対応）
- WebSocketサブスクリプション

## 基本設定

### settings.py

```python
INSTALLED_APPS = [
    # ...
    'graphene_django',
]

GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
}
```

### スキーマの作成

```python
# myproject/schema.py
import graphene
from graphene_django import DjangoObjectType
from myapp.models import Book

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

class Query(graphene.ObjectType):
    books = graphene.List(BookType)
    book = graphene.Field(BookType, id=graphene.ID(required=True))

    def resolve_books(self, info):
        return Book.objects.all()

    def resolve_book(self, info, id):
        return Book.objects.get(pk=id)

schema = graphene.Schema(query=Query)
```

### URLの設定

```python
from django.urls import path
from graphene_django.views import GraphQLView

urlpatterns = [
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]
```

## ミックスイン

### ModelTypeMixin

DjangoObjectTypeを拡張するミックスイン:

```python
from apibase.graphql.mixins import ModelTypeMixin
from graphene_django import DjangoObjectType

class BookType(ModelTypeMixin, DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'
```

### 提供される機能

- 権限チェック
- フィルタリング
- ページネーション

## フィールド

### DjangoListField拡張

リスト取得の拡張:

```python
from apibase.graphql.fields import DjangoListField

class Query(graphene.ObjectType):
    books = DjangoListField(BookType)
```

### DjangoFilterConnectionField

django-filterとの統合:

```python
from apibase.graphql.fields import DjangoFilterConnectionField

class Query(graphene.ObjectType):
    books = DjangoFilterConnectionField(BookType)
```

## コネクション

Relay仕様のコネクション:

```python
from apibase.graphql.connections import Connection, CountableConnection

class BookConnection(CountableConnection):
    class Meta:
        node = BookType

class Query(graphene.ObjectType):
    books = graphene.relay.ConnectionField(BookConnection)
```

### CountableConnection

総件数を含むコネクション:

```graphql
query {
  books(first: 10) {
    totalCount
    edges {
      node {
        id
        title
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## フィルタリング

### FilterSetとの統合

```python
from apibase.filters import BaseFilter, WordFilter

class BookFilter(BaseFilter):
    search = WordFilter(lookups=['title', 'author__name'])

    class Meta:
        model = Book
        fields = {
            'title': ['exact', 'contains'],
            'published_date': ['exact', 'gte', 'lte'],
        }

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'
        filterset_class = BookFilter
```

GraphQLクエリ:

```graphql
query {
  books(search: "Django", publishedDate_Gte: "2024-01-01") {
    id
    title
    author {
      name
    }
  }
}
```

## ミューテーション

### 基本的なミューテーション

```python
class CreateBook(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        author_id = graphene.ID(required=True)

    book = graphene.Field(BookType)

    def mutate(self, info, title, author_id):
        author = Author.objects.get(pk=author_id)
        book = Book.objects.create(title=title, author=author)
        return CreateBook(book=book)

class Mutation(graphene.ObjectType):
    create_book = CreateBook.Field()
```

### SerializerMutation

シリアライザを使用したミューテーション:

```python
from graphene_django.rest_framework.mutation import SerializerMutation
from .serializers import BookSerializer

class BookMutation(SerializerMutation):
    class Meta:
        serializer_class = BookSerializer

class Mutation(graphene.ObjectType):
    book = BookMutation.Field()
```

## エンコーダー

### GraphQLJSONEncoder

Django モデルをJSON互換形式にエンコード:

```python
from apibase.graphql.encoders import GraphQLJSONEncoder
import json

data = {'book': book_instance}
json.dumps(data, cls=GraphQLJSONEncoder)
```

## ユーティリティ

### resolve_qs

QuerySetを安全に解決:

```python
from apibase.graphql.utils import resolve_qs

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

    @classmethod
    def get_queryset(cls, queryset, info):
        return resolve_qs(queryset, info)
```

## 次のステップ

- [GraphQL型定義](graphql-types.md)
- [GraphQL API構築チュートリアル](../tutorials/graphql-api.md)
- [GraphQL Nodeの実例](../examples/graphql-node.md)
