# GraphQL API構築

このチュートリアルでは、apibaseを使ってGraphQL APIを構築します。

## ゴール

- GraphQL スキーマの作成
- Query の実装
- Mutation の実装
- フィルタリングの設定

## 1. セットアップ

### 依存関係のインストール

```bash
pip install graphene-django
```

### settings.py の設定

```python
INSTALLED_APPS = [
    # ...
    'graphene_django',
]

GRAPHENE = {
    'SCHEMA': 'bookstore.schema.schema',
}
```

## 2. 型定義

### books/api/gql/types.py

```python
import graphene
from graphene_django import DjangoObjectType
from graphene import relay

from ...models import Author, Category, Book


class AuthorType(DjangoObjectType):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'bio', 'books']
        interfaces = (relay.Node,)


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'books']
        interfaces = (relay.Node,)


class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'category',
            'isbn', 'price', 'published_date',
            'description', 'is_available',
            'created_at', 'updated_at'
        ]
        interfaces = (relay.Node,)

    # カスタムフィールド
    formatted_price = graphene.String()

    def resolve_formatted_price(self, info):
        return f"¥{self.price:,}"
```

## 3. Query の実装

### books/api/gql/queries.py

```python
import graphene
from graphene_django.filter import DjangoFilterConnectionField

from ...models import Author, Category, Book
from ..filters import AuthorFilter, BookFilter
from .types import AuthorType, CategoryType, BookType


class Query(graphene.ObjectType):
    # 単一オブジェクトの取得
    author = graphene.Field(AuthorType, id=graphene.ID(required=True))
    category = graphene.Field(CategoryType, id=graphene.ID(required=True))
    book = graphene.Field(BookType, id=graphene.ID(required=True))

    # リストの取得
    authors = graphene.List(
        AuthorType,
        search=graphene.String(),
        limit=graphene.Int()
    )
    categories = graphene.List(CategoryType)
    books = graphene.List(
        BookType,
        search=graphene.String(),
        author_id=graphene.ID(),
        category_id=graphene.ID(),
        is_available=graphene.Boolean(),
        limit=graphene.Int()
    )

    # Relay Connection（ページネーション）
    all_books = DjangoFilterConnectionField(
        BookType,
        filterset_class=BookFilter
    )

    def resolve_author(self, info, id):
        try:
            return Author.objects.get(pk=id)
        except Author.DoesNotExist:
            return None

    def resolve_category(self, info, id):
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None

    def resolve_book(self, info, id):
        try:
            return Book.objects.select_related('author', 'category').get(pk=id)
        except Book.DoesNotExist:
            return None

    def resolve_authors(self, info, search=None, limit=None):
        qs = Author.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        if limit:
            qs = qs[:limit]
        return qs

    def resolve_categories(self, info):
        return Category.objects.all()

    def resolve_books(self, info, search=None, author_id=None,
                      category_id=None, is_available=None, limit=None):
        qs = Book.objects.select_related('author', 'category').all()

        if search:
            qs = qs.filter(title__icontains=search)
        if author_id:
            qs = qs.filter(author_id=author_id)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if is_available is not None:
            qs = qs.filter(is_available=is_available)
        if limit:
            qs = qs[:limit]

        return qs
```

## 4. Mutation の実装

### books/api/gql/mutations.py

```python
import graphene
from graphene_django.rest_framework.mutation import SerializerMutation

from ...models import Author, Category, Book
from ..serializers import AuthorSerializer, BookSerializer
from .types import AuthorType, CategoryType, BookType


# Input型の定義
class AuthorInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String()
    bio = graphene.String()


class BookInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    author_id = graphene.ID(required=True)
    category_id = graphene.ID()
    isbn = graphene.String(required=True)
    price = graphene.Int(required=True)
    published_date = graphene.Date(required=True)
    description = graphene.String()
    is_available = graphene.Boolean()


# 著者の作成
class CreateAuthor(graphene.Mutation):
    class Arguments:
        input = AuthorInput(required=True)

    author = graphene.Field(AuthorType)
    ok = graphene.Boolean()

    def mutate(self, info, input):
        author = Author.objects.create(**input)
        return CreateAuthor(author=author, ok=True)


# 著者の更新
class UpdateAuthor(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = AuthorInput(required=True)

    author = graphene.Field(AuthorType)
    ok = graphene.Boolean()

    def mutate(self, info, id, input):
        try:
            author = Author.objects.get(pk=id)
            for key, value in input.items():
                if value is not None:
                    setattr(author, key, value)
            author.save()
            return UpdateAuthor(author=author, ok=True)
        except Author.DoesNotExist:
            return UpdateAuthor(author=None, ok=False)


# 著者の削除
class DeleteAuthor(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            author = Author.objects.get(pk=id)
            author.delete()
            return DeleteAuthor(ok=True)
        except Author.DoesNotExist:
            return DeleteAuthor(ok=False)


# 書籍の作成
class CreateBook(graphene.Mutation):
    class Arguments:
        input = BookInput(required=True)

    book = graphene.Field(BookType)
    ok = graphene.Boolean()

    def mutate(self, info, input):
        input_data = dict(input)
        input_data['author_id'] = input_data.pop('author_id')
        if 'category_id' in input_data:
            input_data['category_id'] = input_data.pop('category_id')

        book = Book.objects.create(**input_data)
        return CreateBook(book=book, ok=True)


# シリアライザを使用したMutation
class BookMutation(SerializerMutation):
    class Meta:
        serializer_class = BookSerializer
        model_operations = ['create', 'update']
        lookup_field = 'id'


class Mutation(graphene.ObjectType):
    create_author = CreateAuthor.Field()
    update_author = UpdateAuthor.Field()
    delete_author = DeleteAuthor.Field()
    create_book = CreateBook.Field()

    # SerializerMutationを使用
    book = BookMutation.Field()
```

## 5. スキーマの統合

### bookstore/schema.py

```python
import graphene
from books.api.gql.queries import Query as BookQuery
from books.api.gql.mutations import Mutation as BookMutation


class Query(BookQuery, graphene.ObjectType):
    pass


class Mutation(BookMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
```

## 6. URLの設定

### bookstore/urls.py

```python
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # ...
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
```

## 7. GraphQLクエリの実行

### 著者一覧の取得

```graphql
query {
  authors {
    id
    name
    email
    books {
      id
      title
    }
  }
}
```

### 書籍の検索

```graphql
query {
  books(search: "Django", isAvailable: true) {
    id
    title
    formattedPrice
    author {
      name
    }
    category {
      name
    }
  }
}
```

### ページネーション付きクエリ

```graphql
query {
  allBooks(first: 10, title_Icontains: "入門") {
    edges {
      node {
        id
        title
        price
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### 著者の作成

```graphql
mutation {
  createAuthor(input: {
    name: "山田太郎"
    email: "yamada@example.com"
    bio: "Pythonプログラマー"
  }) {
    ok
    author {
      id
      name
    }
  }
}
```

### 書籍の作成

```graphql
mutation {
  createBook(input: {
    title: "GraphQL入門"
    authorId: "1"
    isbn: "9784123456789"
    price: 3500
    publishedDate: "2024-03-01"
    description: "GraphQLの基礎から実践まで"
  }) {
    ok
    book {
      id
      title
      formattedPrice
    }
  }
}
```

## 8. 認証の追加

### 認証が必要なクエリ

```python
class Query(graphene.ObjectType):
    my_books = graphene.List(BookType)

    def resolve_my_books(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('認証が必要です')
        return Book.objects.filter(owner=user)
```

### 認証が必要なMutation

```python
class CreateBook(graphene.Mutation):
    class Arguments:
        input = BookInput(required=True)

    book = graphene.Field(BookType)
    ok = graphene.Boolean()

    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('認証が必要です')

        book = Book.objects.create(owner=user, **input)
        return CreateBook(book=book, ok=True)
```

## 次のステップ

- [GraphQL統合ガイド](../guides/graphql.md)
- [実例: GraphQL](real-world-graphql.md)
