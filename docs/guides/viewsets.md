# ViewSet活用ガイド

apibaseは、Django REST FrameworkのViewSetを拡張した`BaseModelViewSet`を提供します。

## 概要

`BaseModelViewSet`は以下の機能を提供します:

- バッチ作成・更新
- ファイルダウンロード
- CSVエクスポート対応
- カスタムページネーション

## 基本的な使い方

```python
from apibase.viewsets import BaseModelViewSet
from apibase.serializers import BaseModelSerializer
from .models import Product

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'endpoint', 'urn', 'display']

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
```

## バッチ操作

### バッチ作成

複数のレコードを一度に作成できます:

```python
# POST /api/products/batch_create/
[
    {"name": "Product 1", "price": 100},
    {"name": "Product 2", "price": 200}
]
```

### バッチ更新

複数のレコードを一度に更新できます:

```python
# PATCH /api/products/batch_update/
[
    {"id": 1, "price": 150},
    {"id": 2, "price": 250}
]
```

## ファイルダウンロード

`DownloadMixin`を使用すると、FileFieldのダウンロードエンドポイントが自動的に追加されます。

### 単一レコードからのダウンロード

```
GET /api/products/{id}/{field_name}/download/
```

### ストレージパスからのダウンロード

```
GET /api/products/storage/{field_name}/{file_path}
```

### カスタマイズ

ダウンロードファイル名をカスタマイズできます:

```python
class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_download_filefield_name(self, instance, field):
        """ダウンロードファイル名を生成"""
        return f"{instance.name}_{field.field.name}.pdf"
```

## CSVエクスポート

CSVレンダラーとの統合:

```python
class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    fields_query = 'fields'  # クエリパラメータ名
```

リクエスト:

```bash
curl -H "Accept: text/csv" \
  "http://localhost:8000/api/products/?fields=id,name,price"
```

レスポンス:

```csv
id,name,price
1,Product 1,100
2,Product 2,200
```

### フィールドラベルのカスタマイズ

シリアライザでラベルを設定すると、CSVヘッダーに使用されます:

```python
class ProductSerializer(BaseModelSerializer):
    name = serializers.CharField(label='商品名')
    price = serializers.IntegerField(label='価格')

    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
```

## ViewSetMixin

`ViewSetMixin`はユーティリティメソッドを提供します:

### パーミッション取得

```python
class ProductViewSet(BaseModelViewSet, ViewSetMixin):
    permission_classes = [MyCustomPermission]

# ViewSetに関連付けられたパーミッションを取得
permissions = ProductViewSet.permissions()
```

### 安全なメソッドの判定

```python
def perform_create(self, serializer):
    if self.is_safe_method:
        # GET, HEAD, OPTIONS の場合
        pass
    else:
        # POST, PUT, PATCH, DELETE の場合
        serializer.save(created_by=self.request.user)
```

## カスタムアクション

追加のアクションを定義できます:

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """商品を公開状態にする"""
        product = self.get_object()
        product.is_published = True
        product.save()
        return Response({'status': 'published'})

    @action(detail=False, methods=['get'])
    def published(self, request):
        """公開済み商品の一覧"""
        published = self.queryset.filter(is_published=True)
        serializer = self.get_serializer(published, many=True)
        return Response(serializer.data)
```

## ページネーションのカスタマイズ

```python
from apibase.paginations import Pagination

class LargeResultsSetPagination(Pagination):
    page_size = 100
    max_page_size = 1000

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = LargeResultsSetPagination
```

## 次のステップ

- [Serializer活用ガイド](serializers.md)
- [フィルタリング機能](filters.md)
- [バッチ操作](batch-operations.md)
