# GraphQL Node

Relay仕様のNode実装例です。

## 型定義

```python
# products/api/gql/types.py
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from apibase.graphql.connections import CountableConnection
from ...models import Product, Category

class CategoryNode(DjangoObjectType):
    class Meta:
        model = Category
        interfaces = (relay.Node,)
        fields = ['id', 'name', 'slug', 'products']

class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = ['id', 'name', 'price', 'stock', 'category', 'created_at']
        filter_fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'category': ['exact'],
        }
        connection_class = CountableConnection

    formatted_price = graphene.String()
    is_available = graphene.Boolean()

    def resolve_formatted_price(self, info):
        return f"¥{self.price:,}"

    def resolve_is_available(self, info):
        return self.stock > 0

    @classmethod
    def get_queryset(cls, queryset, info):
        """権限フィルタリング"""
        if not info.context.user.is_authenticated:
            return queryset.filter(is_published=True)
        return queryset

    @classmethod
    def get_node(cls, info, id):
        """個別取得時のフック"""
        try:
            product = Product.objects.get(pk=id)
            if cls.can_view(info, product):
                return product
        except Product.DoesNotExist:
            pass
        return None

    @classmethod
    def can_view(cls, info, product):
        if product.is_published:
            return True
        return info.context.user.is_staff
```

## Query

```python
# products/api/gql/queries.py
import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from .types import ProductNode, CategoryNode

class Query(graphene.ObjectType):
    # Global IDで単一取得
    product = relay.Node.Field(ProductNode)
    category = relay.Node.Field(CategoryNode)

    # コネクション（ページネーション対応）
    products = DjangoFilterConnectionField(ProductNode)
    categories = DjangoFilterConnectionField(CategoryNode)

    # カスタムリゾルバー
    def resolve_products(self, info, **kwargs):
        return Product.objects.select_related('category').all()
```

## クエリ例

### Global IDで取得

```graphql
query {
  product(id: "UHJvZHVjdE5vZGU6MQ==") {
    id
    name
    formattedPrice
    isAvailable
    category {
      name
    }
  }
}
```

### ページネーション

```graphql
query {
  products(first: 10) {
    totalCount
    edges {
      node {
        id
        name
        price
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### フィルタリング

```graphql
query {
  products(
    first: 10
    name_Icontains: "ノート"
    price_Gte: 1000
    price_Lte: 5000
  ) {
    edges {
      node {
        id
        name
        formattedPrice
      }
    }
  }
}
```

### 次ページの取得

```graphql
query {
  products(first: 10, after: "YXJyYXljb25uZWN0aW9uOjk=") {
    edges {
      node {
        id
        name
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## node Query

任意の型をGlobal IDで取得:

```graphql
query {
  node(id: "UHJvZHVjdE5vZGU6MQ==") {
    id
    ... on ProductNode {
      name
      price
    }
    ... on CategoryNode {
      name
      slug
    }
  }
}
```

## Global ID の変換

```python
from graphene import relay

# モデルIDからGlobal IDへ
global_id = relay.Node.to_global_id('ProductNode', 1)
# "UHJvZHVjdE5vZGU6MQ=="

# Global IDからモデルIDへ
type_name, model_id = relay.Node.from_global_id("UHJvZHVjdE5vZGU6MQ==")
# ('ProductNode', '1')
```
