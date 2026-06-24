# graphql.connections

Relayコネクションを提供するモジュールです。

## クラス

### Connection

基本的なRelayコネクションクラスです。

```python
from apibase.graphql.connections import Connection
```

---

### CountableConnection

総件数を含むコネクションクラスです。

```python
from apibase.graphql.connections import CountableConnection
```

**フィールド**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `totalCount` | `Int` | 総件数 |

**使用例**

```python
from apibase.graphql.connections import CountableConnection

class BookConnection(CountableConnection):
    class Meta:
        node = BookType

class Query(graphene.ObjectType):
    books = graphene.relay.ConnectionField(BookConnection)
```

GraphQLクエリ:

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

レスポンス:

```json
{
  "data": {
    "books": {
      "totalCount": 100,
      "edges": [
        {"node": {"id": "1", "title": "Book 1"}},
        {"node": {"id": "2", "title": "Book 2"}}
      ],
      "pageInfo": {
        "hasNextPage": true,
        "endCursor": "YXJyYXljb25uZWN0aW9uOjk="
      }
    }
  }
}
```

---

## 使用例

### カスタムコネクション

```python
from apibase.graphql.connections import CountableConnection
import graphene

class BookConnection(CountableConnection):
    class Meta:
        node = BookType

    # カスタムフィールド
    total_price = graphene.Decimal()

    def resolve_total_price(root, info):
        from django.db.models import Sum
        if hasattr(root, 'iterable'):
            return root.iterable.aggregate(total=Sum('price'))['total']
        return None
```

### Relay Node

```python
from graphene import relay
from graphene_django import DjangoObjectType

class BookNode(DjangoObjectType):
    class Meta:
        model = Book
        interfaces = (relay.Node,)
        connection_class = CountableConnection

class Query(graphene.ObjectType):
    book = relay.Node.Field(BookNode)
    books = relay.ConnectionField(BookNode.connection)
```
