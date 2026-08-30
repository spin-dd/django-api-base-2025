# permissions

権限クラスを提供するモジュールです。

## クラス

### Permission

Djangoパーミッションと統合された権限クラスです。

```python
from apibase.permissions import Permission
```

**継承元**

- `rest_framework.permissions.BasePermission`

**属性**

| 属性 | 型 | 説明 |
|-----|-----|------|
| `PERM_CODE` | `str` | Django権限コード（例: `'app.change_model'`） |

**使用例**

```python
from apibase.permissions import Permission

class CanEditProduct(Permission):
    PERM_CODE = 'products.change_product'

class ProductViewSet(BaseModelViewSet):
    permission_classes = [CanEditProduct]
```

---

## 関数

### is_safe_method

```python
def is_safe_method(request) -> bool
```

リクエストが安全なメソッド（GET, HEAD, OPTIONS）かどうかを判定します。

**引数**

- `request` - リクエストオブジェクト

**戻り値**

- `bool` - 安全なメソッドの場合True

**使用例**

```python
from apibase.permissions import is_safe_method

def my_view(request):
    if is_safe_method(request):
        # 読み取り操作
        pass
    else:
        # 書き込み操作
        pass
```

---

## 使用例

### 基本的な権限設定

```python
from rest_framework.permissions import IsAuthenticated
from apibase.permissions import Permission

class CanManageProduct(Permission):
    PERM_CODE = 'products.manage_product'

class ProductViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated, CanManageProduct]
```

### アクションごとの権限

```python
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

class ProductViewSet(BaseModelViewSet):
    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        elif self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
```

### 安全なメソッドの判定

```python
class ProductViewSet(BaseModelViewSet):
    def get_queryset(self):
        if self.is_safe_method:
            # 読み取り時は全件
            return Product.objects.all()
        else:
            # 書き込み時は自分のデータのみ
            return Product.objects.filter(owner=self.request.user)
```

### ViewSetでのパーミッション取得

```python
from apibase.viewsets import BaseModelViewSet

class ProductViewSet(BaseModelViewSet):
    permission_classes = [CanManageProduct]

# ViewSetに関連するDjango Permissionを取得
permissions = ProductViewSet.permissions()
# [<Permission: products.manage_product>]
```

### オブジェクトレベルの権限

```python
from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class ProductViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
```
