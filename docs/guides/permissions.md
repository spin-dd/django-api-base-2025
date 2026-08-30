# 権限管理

apibaseは、Django REST Frameworkの権限システムを拡張した機能を提供します。

## 概要

`apibase.permissions`モジュールは以下を提供します:

- Djangoパーミッションとの統合
- 安全なメソッドの判定
- ViewSetとの統合

## 基本的な使い方

### Permission クラス

```python
from apibase.permissions import Permission

class CanEditProduct(Permission):
    PERM_CODE = 'products.change_product'

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [CanEditProduct]
```

### パーミッションの取得

ViewSetに関連付けられたパーミッションを取得:

```python
# ViewSetMixinのpermissionsメソッド
permissions = ProductViewSet.permissions()
# [<Permission: products.change_product>]
```

## 安全なメソッドの判定

### is_safe_method

HTTPメソッドが安全（読み取り専用）かどうかを判定:

```python
from apibase.permissions import is_safe_method

def my_view(request):
    if is_safe_method(request):
        # GET, HEAD, OPTIONS
        pass
    else:
        # POST, PUT, PATCH, DELETE
        pass
```

### ViewSet内での使用

```python
class ProductViewSet(BaseModelViewSet):
    def get_queryset(self):
        if self.is_safe_method:
            return Product.objects.all()
        else:
            # 書き込み操作は自分のデータのみ
            return Product.objects.filter(owner=self.request.user)
```

## カスタムパーミッション

### 基本的なカスタムパーミッション

```python
from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class ProductViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
```

### PERM_CODEとの組み合わせ

```python
from apibase.permissions import Permission

class IsProductManager(Permission):
    PERM_CODE = 'products.manage_product'

    def has_permission(self, request, view):
        if is_safe_method(request):
            return True
        return super().has_permission(request, view)
```

## アクションごとの権限

### get_permissions

```python
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

class ProductViewSet(BaseModelViewSet):
    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
```

### permission_classes_by_action

```python
class ProductViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAdminUser],
        'update': [IsAdminUser],
        'destroy': [IsAdminUser],
    }

    def get_permissions(self):
        permission_classes = self.permission_classes_by_action.get(
            self.action,
            self.permission_classes
        )
        return [permission() for permission in permission_classes]
```

## オブジェクトレベルの権限

### has_object_permission

```python
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # 読み取り操作は全員許可
        if request.method in SAFE_METHODS:
            return True
        # 書き込み操作はオーナーのみ
        return obj.owner == request.user
```

### check_object_permissions

```python
class ProductViewSet(BaseModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 明示的に権限チェック
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

## Djangoパーミッションとの統合

### DjangoModelPermissions

```python
from rest_framework.permissions import DjangoModelPermissions

class ProductViewSet(BaseModelViewSet):
    permission_classes = [DjangoModelPermissions]
```

これにより以下のマッピングが適用されます:

| HTTPメソッド | 必要なパーミッション |
|-------------|---------------------|
| GET | `view_product` |
| POST | `add_product` |
| PUT/PATCH | `change_product` |
| DELETE | `delete_product` |

### カスタムパーミッションマッピング

```python
class CustomModelPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
```

## GraphQLでの権限

### Query/Mutationでの権限チェック

```python
class Query(graphene.ObjectType):
    products = graphene.List(ProductType)

    def resolve_products(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return Product.objects.none()
        if user.is_staff:
            return Product.objects.all()
        return Product.objects.filter(is_public=True)
```

### ObjectTypeでの権限

```python
class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'secret_info']

    def resolve_secret_info(self, info):
        if info.context.user.is_staff:
            return self.secret_info
        return None
```

## パーミッションのテスト

```python
from rest_framework.test import APITestCase
from django.contrib.auth.models import Permission

class ProductPermissionTests(APITestCase):
    def test_create_requires_permission(self):
        user = User.objects.create_user('user', 'user@example.com', 'pass')
        self.client.force_authenticate(user)

        response = self.client.post('/api/products/', {'name': 'Test'})
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission(self):
        user = User.objects.create_user('user', 'user@example.com', 'pass')
        permission = Permission.objects.get(codename='add_product')
        user.user_permissions.add(permission)
        self.client.force_authenticate(user)

        response = self.client.post('/api/products/', {'name': 'Test'})
        self.assertEqual(response.status_code, 201)
```

## 次のステップ

- [APIリファレンス: permissions](../reference/permissions.md)
- [テストの書き方](../tutorials/testing.md)
