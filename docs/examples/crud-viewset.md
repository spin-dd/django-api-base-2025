# CRUD ViewSet

基本的なCRUD（Create, Read, Update, Delete）操作の実装例です。

## モデル

```python
# products/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField('商品名', max_length=200)
    price = models.PositiveIntegerField('価格')
    stock = models.PositiveIntegerField('在庫', default=0)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.name
```

## シリアライザ

```python
# products/api/serializers.py
from apibase.serializers import BaseModelSerializer
from ..models import Product

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'stock', 'is_active',
            'created_at', 'updated_at',
            'endpoint', 'urn', 'display'
        ]
        read_only_fields = ['created_at', 'updated_at']
```

## フィルタ

```python
# products/api/filters.py
from apibase.filters import BaseFilter, WordFilter

class ProductFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['name'],
    )

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'contains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
            'is_active': ['exact'],
        }
```

## ViewSet

```python
# products/api/viewsets.py
from apibase.viewsets import BaseModelViewSet
from ..models import Product
from .serializers import ProductSerializer
from .filters import ProductFilter

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    search_fields = ['name']
```

## URL設定

```python
# products/api/urls.py
from rest_framework.routers import DefaultRouter
from .viewsets import ProductViewSet

router = DefaultRouter()
router.register('products', ProductViewSet)

urlpatterns = router.urls
```

## APIの使用例

### 一覧取得

```bash
curl http://localhost:8000/api/products/
```

レスポンス:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "商品A",
            "price": 1000,
            "stock": 10,
            "is_active": true,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "endpoint": "http://localhost:8000/api/products/1/",
            "urn": "urn:products:product:1",
            "display": "商品A"
        }
    ]
}
```

### 詳細取得

```bash
curl http://localhost:8000/api/products/1/
```

### 作成

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "新商品", "price": 1500, "stock": 5}'
```

### 更新

```bash
curl -X PATCH http://localhost:8000/api/products/1/ \
  -H "Content-Type: application/json" \
  -d '{"price": 1200}'
```

### 削除

```bash
curl -X DELETE http://localhost:8000/api/products/1/
```

### 検索

```bash
curl "http://localhost:8000/api/products/?search=商品"
```

### フィルタリング

```bash
curl "http://localhost:8000/api/products/?price__gte=1000&is_active=true"
```

### ソート

```bash
curl "http://localhost:8000/api/products/?ordering=-price"
```
