# GraphQL型定義

apibaseでのGraphQL型定義について説明します。

## 基本的な型定義

### DjangoObjectType

```python
from graphene_django import DjangoObjectType
from .models import Book, Author

class AuthorType(DjangoObjectType):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email']

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'published_date']
```

## gql.types モジュール

apibaseは `apibase.gql.types` でGraphQL型のユーティリティを提供します。

### 使用例

```python
from apibase.gql.types import create_type_from_model

# モデルから自動的に型を生成
BookType = create_type_from_model(Book, fields=['id', 'title', 'author'])
```

## カスタムスカラー型

### Date / DateTime

```python
import graphene
from graphene.types import DateTime, Date

class BookType(DjangoObjectType):
    published_date = Date()
    created_at = DateTime()

    class Meta:
        model = Book
        fields = '__all__'
```

### JSON型

```python
from graphene.types import JSONString

class BookType(DjangoObjectType):
    metadata = JSONString()

    class Meta:
        model = Book
        fields = '__all__'

    def resolve_metadata(self, info):
        return self.metadata  # JSONField
```

## リレーション

### 1対多

```python
class AuthorType(DjangoObjectType):
    class Meta:
        model = Author
        fields = ['id', 'name', 'books']

    # 明示的にリレーションを定義
    books = graphene.List(lambda: BookType)

    def resolve_books(self, info):
        return self.book_set.all()
```

### 多対多

```python
class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = ['id', 'title', 'tags']

    tags = graphene.List(lambda: TagType)

    def resolve_tags(self, info):
        return self.tags.all()
```

## フィルタリング対応型

```python
from apibase.filters import BaseFilter, WordFilter

class BookFilter(BaseFilter):
    search = WordFilter(lookups=['title', 'author__name'])

    class Meta:
        model = Book
        fields = {
            'title': ['exact', 'contains'],
            'published_date': ['gte', 'lte'],
        }

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'
        filterset_class = BookFilter
```

## Relay Node

Relayの仕様に準拠したNode:

```python
from graphene import relay
from graphene_django import DjangoObjectType

class BookNode(DjangoObjectType):
    class Meta:
        model = Book
        interfaces = (relay.Node,)
        fields = '__all__'

class Query(graphene.ObjectType):
    book = relay.Node.Field(BookNode)
    books = DjangoFilterConnectionField(BookNode)
```

### Global ID

```graphql
query {
  # Global IDで取得
  book(id: "Qm9va05vZGU6MQ==") {
    id
    title
  }

  # ページネーション
  books(first: 10) {
    edges {
      node {
        id
        title
      }
    }
  }
}
```

## カスタムリゾルバー

### インスタンスメソッド

```python
class BookType(DjangoObjectType):
    summary = graphene.String()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author']

    def resolve_summary(self, info):
        return f"{self.title} by {self.author.name}"
```

### 静的リゾルバー

```python
class BookType(DjangoObjectType):
    is_available = graphene.Boolean()

    class Meta:
        model = Book
        fields = '__all__'

    @staticmethod
    def resolve_is_available(root, info):
        return root.stock > 0
```

## 権限とフィルタリング

### get_queryset

```python
class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if user.is_staff:
            return queryset
        return queryset.filter(is_published=True)
```

### get_node

```python
class BookNode(DjangoObjectType):
    class Meta:
        model = Book
        interfaces = (relay.Node,)
        fields = '__all__'

    @classmethod
    def get_node(cls, info, id):
        try:
            book = Book.objects.get(pk=id)
            if book.can_view(info.context.user):
                return book
        except Book.DoesNotExist:
            pass
        return None
```

## 入力型

### InputObjectType

```python
class BookInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    author_id = graphene.ID(required=True)
    published_date = graphene.Date()

class CreateBook(graphene.Mutation):
    class Arguments:
        input = BookInput(required=True)

    book = graphene.Field(BookType)

    def mutate(self, info, input):
        book = Book.objects.create(**input)
        return CreateBook(book=book)
```

## Enum型

```python
import graphene

class BookStatus(graphene.Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

class BookType(DjangoObjectType):
    status = graphene.Field(BookStatus)

    class Meta:
        model = Book
        fields = '__all__'

    def resolve_status(self, info):
        return self.status
```

## Union型

```python
class SearchResult(graphene.Union):
    class Meta:
        types = (BookType, AuthorType)

class Query(graphene.ObjectType):
    search = graphene.List(SearchResult, query=graphene.String())

    def resolve_search(self, info, query):
        books = Book.objects.filter(title__contains=query)
        authors = Author.objects.filter(name__contains=query)
        return list(books) + list(authors)
```

## 次のステップ

- [GraphQL API構築チュートリアル](../tutorials/graphql-api.md)
- [GraphQL Queryの実例](../examples/graphql-query.md)
