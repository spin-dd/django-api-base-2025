# マイグレーションガイド

既存プロジェクトへのapibase導入とバージョンアップのガイドです。

## 既存プロジェクトへの導入

### 1. 依存関係の追加

```bash
pip install apibase
```

### 2. 既存ViewSetの移行

**Before:**
```python
from rest_framework import viewsets

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
```

**After:**
```python
from apibase.viewsets import BaseModelViewSet

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
```

### 3. 既存Serializerの移行

**Before:**
```python
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
```

**After:**
```python
from apibase.serializers import BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'endpoint', 'urn', 'display']
```

### 4. 既存Filterの移行

**Before:**
```python
import django_filters

class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = ['name', 'price']
```

**After:**
```python
from apibase.filters import BaseFilter

class ProductFilter(BaseFilter):
    class Meta:
        model = Product
        fields = {'name': ['exact', 'contains'], 'price': ['exact', 'gte', 'lte']}
```

## バージョンアップ

### v0.1.x → v0.2.x

#### 破壊的変更

1. **Pagination設定の変更**

   `PAGE_SIZE`のデフォルト値が変更されました。明示的に設定してください:

   ```python
   REST_FRAMEWORK = {
       'PAGE_SIZE': 20,
   }
   ```

2. **ネストシリアライザの動作変更**

   `nested_fields`に指定したフィールドは、`validated_data`から自動的に除外されるようになりました。

#### 新機能の活用

1. **バッチ操作**

   ```python
   # 新しいエンドポイントが追加されます
   POST /api/products/batch_create/
   PATCH /api/products/batch_update/
   ```

2. **WordFilter**

   日本語検索が改善されました:

   ```python
   class ProductFilter(BaseFilter):
       search = WordFilter(lookups=['name', 'description'])
   ```

### 移行チェックリスト

- [ ] 依存関係を更新
- [ ] テストを実行
- [ ] 非推奨警告を確認
- [ ] 破壊的変更に対応
- [ ] 新機能を検討

## 段階的な移行

大規模プロジェクトでは段階的な移行を推奨:

### フェーズ1: Filterの移行

最もリスクが低いFilterから移行:

```python
from apibase.filters import BaseFilter

class ProductFilter(BaseFilter):
    class Meta:
        model = Product
        fields = {'name': ['contains']}
```

### フェーズ2: Serializerの移行

新しいフィールドが追加されることに注意:

```python
from apibase.serializers import BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'endpoint', 'urn', 'display']
```

### フェーズ3: ViewSetの移行

バッチ操作のエンドポイントが追加されることに注意:

```python
from apibase.viewsets import BaseModelViewSet

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
```

## トラブルシューティング

### インポートエラー

```python
# 古い
from apibase import ViewSet  # エラー

# 新しい
from apibase.viewsets import BaseModelViewSet
```

### フィールドの不一致

シリアライザのフィールドとモデルのフィールドを確認してください。

### テストの失敗

新しいフィールド（endpoint, urn, display）がレスポンスに含まれるため、テストの期待値を更新してください。
