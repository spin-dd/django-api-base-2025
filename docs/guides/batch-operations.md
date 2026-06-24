# バッチ操作

apibaseは、複数レコードの一括作成・更新機能を提供します。

## 概要

`BaseModelViewSet`は以下のバッチ操作をサポートします:

- `batch_create`: 複数レコードの一括作成
- `batch_update`: 複数レコードの一括更新

## バッチ作成

### エンドポイント

```
POST /api/products/batch_create/
```

### リクエスト

```json
[
    {"name": "Product 1", "price": 100, "category": "A"},
    {"name": "Product 2", "price": 200, "category": "B"},
    {"name": "Product 3", "price": 300, "category": "A"}
]
```

### レスポンス

```json
[
    {"id": 1, "name": "Product 1", "price": 100, "category": "A"},
    {"id": 2, "name": "Product 2", "price": 200, "category": "B"},
    {"id": 3, "name": "Product 3", "price": 300, "category": "A"}
]
```

### 使用例

```python
import requests

products = [
    {"name": "Product 1", "price": 100},
    {"name": "Product 2", "price": 200},
]

response = requests.post(
    'http://localhost:8000/api/products/batch_create/',
    json=products
)
```

## バッチ更新

### エンドポイント

```
PATCH /api/products/batch_update/
```

### リクエスト

各オブジェクトには識別子（デフォルトは`id`）が必要です:

```json
[
    {"id": 1, "price": 150},
    {"id": 2, "price": 250},
    {"id": 3, "name": "Updated Product 3"}
]
```

### レスポンス

```json
[
    {"id": 1, "name": "Product 1", "price": 150, "category": "A"},
    {"id": 2, "name": "Product 2", "price": 250, "category": "B"},
    {"id": 3, "name": "Updated Product 3", "price": 300, "category": "A"}
]
```

## シリアライザの設定

### BatchSerializerMixin

バッチ更新に対応するため、シリアライザに`BatchSerializerMixin`を追加:

```python
from apibase.serializers import BatchSerializerMixin, BatchListSerializer, BaseModelSerializer

class ProductSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category']
        list_serializer_class = BatchListSerializer
        update_lookup_field = 'id'  # 更新時の識別フィールド
```

### カスタム識別フィールド

`id`以外のフィールドで識別する場合:

```python
class ProductSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'price']
        list_serializer_class = BatchListSerializer
        update_lookup_field = 'sku'  # SKUで識別
```

リクエスト:

```json
[
    {"sku": "PROD-001", "price": 150},
    {"sku": "PROD-002", "price": 250}
]
```

## BatchListSerializer

### カスタマイズ

バッチ更新のロジックをカスタマイズ:

```python
from apibase.serializers import BatchListSerializer

class ProductBatchSerializer(BatchListSerializer):
    def update(self, queryset, all_validated_data):
        # 更新前の処理
        for data in all_validated_data:
            data['updated_at'] = timezone.now()

        return super().update(queryset, all_validated_data)
```

## フィルタリングとの組み合わせ

バッチ更新時にフィルタリングを適用:

```bash
# category=Aの製品のみをバッチ更新
PATCH /api/products/batch_update/?category=A
```

ViewSetでの処理:

```python
class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter

    def update_batch(self, request, *args, **kwargs):
        # filter_queryset でフィルタリングされたクエリセットが使用される
        return super().update_batch(request, *args, **kwargs)
```

## トランザクション

### 自動トランザクション

デフォルトでは、各操作は個別のトランザクションで実行されます。

### 明示的なトランザクション

全体を1つのトランザクションにする場合:

```python
from django.db import transaction

class ProductViewSet(BaseModelViewSet):
    @transaction.atomic
    def batch_create(self, request, *args, **kwargs):
        return super().batch_create(request, *args, **kwargs)

    @transaction.atomic
    def batch_update(self, request, *args, **kwargs):
        return super().batch_update(request, *args, **kwargs)
```

## エラーハンドリング

### バリデーションエラー

```python
# 1件でもエラーがあると全体が失敗
[
    {"name": "Valid Product", "price": 100},
    {"name": "", "price": 200}  # nameが空でエラー
]
```

レスポンス:

```json
[
    {},
    {"name": ["この項目は必須です。"]}
]
```

### 部分的な成功を許可

```python
from rest_framework import status
from rest_framework.response import Response

class ProductViewSet(BaseModelViewSet):
    def create_batch(self, request, *args, **kwargs):
        results = []
        errors = []

        for item in request.data:
            serializer = self.get_serializer(data=item)
            if serializer.is_valid():
                serializer.save()
                results.append(serializer.data)
            else:
                errors.append({
                    'data': item,
                    'errors': serializer.errors
                })

        return Response({
            'created': results,
            'errors': errors
        }, status=status.HTTP_207_MULTI_STATUS)
```

## パフォーマンス

### bulk_create の使用

大量データの作成時は`bulk_create`を使用:

```python
class ProductViewSet(BaseModelViewSet):
    def create_batch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # bulk_createで一括挿入
        products = [Product(**item) for item in serializer.validated_data]
        Product.objects.bulk_create(products)

        return Response(
            self.get_serializer(products, many=True).data,
            status=status.HTTP_201_CREATED
        )
```

### bulk_update の使用

```python
class ProductViewSet(BaseModelViewSet):
    def update_batch(self, request, *args, **kwargs):
        # 既存の実装をオーバーライド
        serializer = self.get_serializer(
            self.filter_queryset(self.get_queryset()),
            data=request.data,
            many=True,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        # bulk_updateで一括更新
        instances = serializer.save()
        Product.objects.bulk_update(instances, ['name', 'price'])

        return Response(serializer.data)
```

## 次のステップ

- [バッチ作成の実例](../examples/batch-create.md)
- [ViewSet活用ガイド](viewsets.md)
