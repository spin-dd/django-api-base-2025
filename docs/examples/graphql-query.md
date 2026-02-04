# GraphQL Query

GraphQLクエリの実装例です。

## 基本的なQuery

```python
# myapp/schema.py
import graphene
from graphene_django import DjangoObjectType
from .models import Book, Author

class AuthorType(DjangoObjectType):
    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'books']

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = ['id', 'title', 'price', 'author', 'published_date']

class Query(graphene.ObjectType):
    # 全件取得
    authors = graphene.List(AuthorType)
    books = graphene.List(BookType)

    # 単一取得
    author = graphene.Field(AuthorType, id=graphene.ID(required=True))
    book = graphene.Field(BookType, id=graphene.ID(required=True))

    def resolve_authors(self, info):
        return Author.objects.all()

    def resolve_books(self, info):
        return Book.objects.select_related('author').all()

    def resolve_author(self, info, id):
        try:
            return Author.objects.get(pk=id)
        except Author.DoesNotExist:
            return None

    def resolve_book(self, info, id):
        try:
            return Book.objects.get(pk=id)
        except Book.DoesNotExist:
            return None
```

## フィルタリング付きQuery

```python
class Query(graphene.ObjectType):
    books = graphene.List(
        BookType,
        search=graphene.String(),
        author_id=graphene.ID(),
        price_min=graphene.Int(),
        price_max=graphene.Int(),
        limit=graphene.Int(),
    )

    def resolve_books(self, info, search=None, author_id=None,
                      price_min=None, price_max=None, limit=None):
        qs = Book.objects.all()

        if search:
            qs = qs.filter(title__icontains=search)
        if author_id:
            qs = qs.filter(author_id=author_id)
        if price_min:
            qs = qs.filter(price__gte=price_min)
        if price_max:
            qs = qs.filter(price__lte=price_max)
        if limit:
            qs = qs[:limit]

        return qs
```

## クエリ例

### 基本クエリ

```graphql
query {
  books {
    id
    title
    price
    author {
      name
    }
  }
}
```

### 単一取得

```graphql
query {
  book(id: "1") {
    id
    title
    price
    publishedDate
    author {
      name
      email
    }
  }
}
```

### フィルタリング

```graphql
query {
  books(search: "Django", priceMin: 1000, priceMax: 5000) {
    id
    title
    price
  }
}
```

### 複数クエリ

```graphql
query {
  authors {
    id
    name
  }
  popularBooks: books(limit: 5) {
    id
    title
  }
}
```

## 集計クエリ

```python
class BookStats(graphene.ObjectType):
    total_count = graphene.Int()
    total_value = graphene.Decimal()
    average_price = graphene.Decimal()

class Query(graphene.ObjectType):
    book_stats = graphene.Field(BookStats)

    def resolve_book_stats(self, info):
        from django.db.models import Count, Sum, Avg

        stats = Book.objects.aggregate(
            total_count=Count('id'),
            total_value=Sum('price'),
            average_price=Avg('price')
        )

        return BookStats(
            total_count=stats['total_count'],
            total_value=stats['total_value'],
            average_price=stats['average_price']
        )
```

```graphql
query {
  bookStats {
    totalCount
    totalValue
    averagePrice
  }
}
```

## 認証付きクエリ

```python
class Query(graphene.ObjectType):
    my_books = graphene.List(BookType)

    def resolve_my_books(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("認証が必要です")
        return Book.objects.filter(owner=user)
```

## 変数の使用

```graphql
query GetBook($bookId: ID!) {
  book(id: $bookId) {
    id
    title
    price
  }
}
```

変数:
```json
{
  "bookId": "1"
}
```

## Fragments

```graphql
fragment BookFields on BookType {
  id
  title
  price
}

query {
  books {
    ...BookFields
    author {
      name
    }
  }
}
```
