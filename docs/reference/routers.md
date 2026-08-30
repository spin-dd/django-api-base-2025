# routers

URLルーターを提供するモジュールです。

## クラス

### Router

カスタムルーター（必要に応じて拡張）

```python
from apibase.routers import Router
```

現在のバージョンでは、Django REST Frameworkの標準ルーターを使用することを推奨します:

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('products', ProductViewSet)
router.register('orders', OrderViewSet)

urlpatterns = router.urls
```

---

## 使用例

### 基本的なルーティング

```python
# myapp/api/urls.py
from rest_framework.routers import DefaultRouter
from .viewsets import ProductViewSet, OrderViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = router.urls
```

### カスタムルーティング

```python
from rest_framework.routers import DefaultRouter, Route

class CustomRouter(DefaultRouter):
    routes = [
        # リスト操作
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # 詳細操作
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
    ]
```

### ネストされたルーティング

```python
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

router = DefaultRouter()
router.register('authors', AuthorViewSet)

# ネストルーター
authors_router = routers.NestedDefaultRouter(router, 'authors', lookup='author')
authors_router.register('books', BookViewSet, basename='author-books')

urlpatterns = router.urls + authors_router.urls
```
