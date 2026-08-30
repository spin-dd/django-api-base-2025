# graphql.fields

GraphQLフィールドを提供するモジュールです。

## クラス

### DjangoListField

Django QuerySetをリストとして返すフィールドです。

```python
from apibase.graphql.fields import DjangoListField
```

**使用例**

```python
import graphene
from apibase.graphql.fields import DjangoListField

class Query(graphene.ObjectType):
    books = DjangoListField(BookType)
```

---

### DjangoFilterConnectionField

django-filterと統合されたコネクションフィールドです。

```python
from apibase.graphql.fields import DjangoFilterConnectionField
```

**使用例**

```python
import graphene
from apibase.graphql.fields import DjangoFilterConnectionField

class Query(graphene.ObjectType):
    books = DjangoFilterConnectionField(BookType)
```

---

## 使用例

### 基本的なリスト取得

```python
class Query(graphene.ObjectType):
    books = DjangoListField(BookType)
    authors = DjangoListField(AuthorType)
```

GraphQLクエリ:

```graphql
query {
  books {
    id
    title
  }
  authors {
    id
    name
  }
}
```

### フィルタリング対応

```python
from apibase.filters import BaseFilter

class BookFilter(BaseFilter):
    class Meta:
        model = Book
        fields = {
            'title': ['exact', 'icontains'],
            'author': ['exact'],
        }

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'
        filterset_class = BookFilter

class Query(graphene.ObjectType):
    books = DjangoFilterConnectionField(BookType)
```

GraphQLクエリ:

```graphql
query {
  books(title_Icontains: "Django", first: 10) {
    edges {
      node {
        id
        title
      }
    }
  }
}
```
