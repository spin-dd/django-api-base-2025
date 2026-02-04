# paginations

ページネーションクラスを提供するモジュールです。

## クラス

### Pagination

デフォルトのページネーションクラスです。

```python
from apibase.paginations import Pagination
```

**継承元**

- `rest_framework.pagination.PageNumberPagination`

**属性**

| 属性 | 値 | 説明 |
|-----|-----|------|
| `page_size` | 設定による | 1ページあたりの件数 |
| `page_size_query_param` | `'page_size'` | ページサイズ指定パラメータ |
| `max_page_size` | 設定による | 最大ページサイズ |

---

## 設定

### REST_FRAMEWORK設定

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
    'PAGE_SIZE': 20,
}
```

---

## レスポンス形式

```json
{
    "count": 100,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [
        {"id": 1, "name": "Product 1"},
        {"id": 2, "name": "Product 2"}
    ]
}
```

---

## 使用例

### ViewSetでの使用

```python
from apibase.viewsets import BaseModelViewSet
from apibase.paginations import Pagination

class LargeResultPagination(Pagination):
    page_size = 100
    max_page_size = 1000

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = LargeResultPagination
```

### ページサイズの指定

```bash
# デフォルトのページサイズ
curl "http://localhost:8000/api/products/"

# ページサイズを指定
curl "http://localhost:8000/api/products/?page_size=50"

# 2ページ目を取得
curl "http://localhost:8000/api/products/?page=2"
```

### ページネーションの無効化

```python
class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = None  # ページネーションを無効化
```

### カーソルベースのページネーション

```python
from rest_framework.pagination import CursorPagination

class ProductCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductCursorPagination
```
