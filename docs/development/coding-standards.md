# コーディング規約

apibaseのコーディング規約について説明します。

## ツール

### Ruff（リンター）

```toml
# pyproject.toml
[tool.ruff]
line-length = 119
select = ["E4", "E7", "E9", "F", "B", "W", "I", "C4", "UP"]
```

実行:

```bash
uv run ruff check apibase
uv run ruff check apibase --fix
```

### Black（フォーマッター）

```bash
uv run black apibase
```

## Python スタイル

### インポート

```python
# 標準ライブラリ
import os
from pathlib import Path

# Django
from django.db import models
from django.contrib.auth.models import User

# サードパーティ
from rest_framework import serializers
import graphene

# ローカル
from .models import Product
from ..utils import helper
```

### 命名規則

| 種類 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `ProductViewSet` |
| 関数/メソッド | snake_case | `get_queryset` |
| 変数 | snake_case | `product_list` |
| 定数 | UPPER_SNAKE_CASE | `DEFAULT_PAGE_SIZE` |
| プライベート | `_prefix` | `_internal_method` |

### ドキュメント文字列

Google スタイルを使用:

```python
def process_data(data, options=None):
    """データを処理する。

    Args:
        data: 処理対象のデータ
        options: オプション設定（オプション）

    Returns:
        処理結果の辞書

    Raises:
        ValueError: データが無効な場合
    """
    pass
```

### 型ヒント

```python
from typing import Optional, List

def get_products(
    category: Optional[str] = None,
    limit: int = 10
) -> List[Product]:
    """商品を取得する"""
    pass
```

## Django スタイル

### モデル

```python
class Product(models.Model):
    """商品モデル"""

    # フィールド
    name = models.CharField('名前', max_length=200)
    price = models.PositiveIntegerField('価格')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # プロパティ
    @property
    def is_available(self):
        return self.stock > 0

    # メソッド
    def apply_discount(self, rate):
        return self.price * (1 - rate)
```

### ViewSet

```python
class ProductViewSet(BaseModelViewSet):
    """商品ViewSet"""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter

    def get_queryset(self):
        """クエリセットを取得"""
        qs = super().get_queryset()
        if self.action == 'list':
            return qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """商品を公開"""
        product = self.get_object()
        product.is_published = True
        product.save()
        return Response({'status': 'published'})
```

### Serializer

```python
class ProductSerializer(BaseModelSerializer):
    """商品シリアライザ"""

    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'category', 'category_name',
            'endpoint', 'urn', 'display'
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('価格は正の値である必要があります')
        return value
```

## エラーハンドリング

```python
# 良い例
try:
    product = Product.objects.get(pk=pk)
except Product.DoesNotExist:
    raise Http404('商品が見つかりません')

# 悪い例
try:
    product = Product.objects.get(pk=pk)
except:  # 裸のexcept
    pass
```

## テストコード

```python
@pytest.mark.django_db
class TestProductViewSet:
    """ProductViewSetのテスト"""

    def test_list_returns_active_products(self, api_client, product_factory):
        """アクティブな商品のみ返すことを確認"""
        # Arrange
        product_factory(is_active=True)
        product_factory(is_active=False)

        # Act
        response = api_client.get('/api/products/')

        # Assert
        assert response.status_code == 200
        assert response.data['count'] == 1
```

## コメント

```python
# TODO: パフォーマンス改善が必要
# FIXME: この処理はN+1問題がある
# NOTE: この動作は仕様による
# HACK: 一時的な回避策
```
