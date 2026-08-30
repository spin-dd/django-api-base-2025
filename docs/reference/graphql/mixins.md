# graphql.mixins

GraphQLミックスインを提供するモジュールです。

## クラス

### ModelTypeMixin

DjangoObjectTypeを拡張するミックスインです。

```python
from apibase.graphql.mixins import ModelTypeMixin
```

**使用例**

```python
from graphene_django import DjangoObjectType
from apibase.graphql.mixins import ModelTypeMixin

class BookType(ModelTypeMixin, DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'
```

---

## 使用例

### 権限フィルタリング

```python
from graphene_django import DjangoObjectType
from apibase.graphql.mixins import ModelTypeMixin

class BookType(ModelTypeMixin, DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user.is_authenticated:
            return queryset.filter(is_public=True)
        return queryset
```

### カスタムリゾルバー

```python
class BookType(ModelTypeMixin, DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

    summary = graphene.String()

    def resolve_summary(self, info):
        return f"{self.title} by {self.author.name}"
```
