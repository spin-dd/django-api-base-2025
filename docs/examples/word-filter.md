# 日本語検索

WordFilterを使用した日本語検索の実装例です。

## 基本的な使用

### フィルタ定義

```python
# customers/api/filters.py
from apibase.filters import BaseFilter, WordFilter

class CustomerFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['name', 'name_kana', 'email', 'phone'],
    )

    class Meta:
        model = Customer
        fields = {}
```

### モデル

```python
# customers/models.py
from django.db import models

class Customer(models.Model):
    name = models.CharField('氏名', max_length=100)
    name_kana = models.CharField('氏名カナ', max_length=100)
    email = models.EmailField('メールアドレス')
    phone = models.CharField('電話番号', max_length=20)
```

## 検索例

### 日本語検索

```bash
# 「山田」で検索
curl "http://localhost:8000/api/customers/?search=山田"
```

### 全角/半角対応

WordFilterは自動的に全角/半角を変換して検索します:

```bash
# 半角数字で検索
curl "http://localhost:8000/api/customers/?search=090"

# 全角数字でも同じ結果
curl "http://localhost:8000/api/customers/?search=０９０"
```

### カタカナ対応

```bash
# 半角カタカナで検索
curl "http://localhost:8000/api/customers/?search=ﾔﾏﾀﾞ"

# 全角カタカナでも同じ結果
curl "http://localhost:8000/api/customers/?search=ヤマダ"
```

### 複数キーワードのAND検索

```bash
# 「山田」AND「東京」で検索（スペース区切り）
curl "http://localhost:8000/api/customers/?search=山田 東京"
```

## カスタマイズ

### 区切り文字の変更

```python
class CustomerFilter(BaseFilter):
    search = WordFilter(
        lookups=['name', 'email'],
        delimiters=r'[\s\u3000,、]+',  # 日本語読点も区切りに
    )
```

### ルックアップ式の変更

```python
class CustomerFilter(BaseFilter):
    search = WordFilter(
        lookups=['name', 'email'],
        lookup_expr='icontains',  # 大文字小文字を無視
    )
```

## 住所検索への応用

```python
class AddressFilter(BaseFilter):
    address_search = WordFilter(
        label='住所検索',
        lookups=['prefecture', 'city', 'town', 'address1', 'address2'],
    )
```

```bash
# 東京都渋谷区を検索
curl "http://localhost:8000/api/addresses/?address_search=東京 渋谷"
```

## 商品検索への応用

```python
class ProductFilter(BaseFilter):
    search = WordFilter(
        label='商品検索',
        lookups=[
            'name',
            'description',
            'category__name',
            'brand__name',
        ],
    )
```

```bash
# 複数フィールドを横断検索
curl "http://localhost:8000/api/products/?search=ノートパソコン Apple"
```

## 関連モデルの検索

```python
class OrderFilter(BaseFilter):
    search = WordFilter(
        lookups=[
            'order_number',
            'customer__name',
            'customer__email',
            'items__product__name',
        ],
        distinct=True,  # 重複を除外
    )
```

## パフォーマンス考慮

### インデックスの追加

```python
class Customer(models.Model):
    name = models.CharField('氏名', max_length=100, db_index=True)
    name_kana = models.CharField('氏名カナ', max_length=100, db_index=True)
```

### PostgreSQL全文検索

大規模データの場合:

```python
from django.contrib.postgres.search import SearchVector

class CustomerFilter(BaseFilter):
    search = django_filters.CharFilter(method='full_text_search')

    def full_text_search(self, queryset, name, value):
        return queryset.annotate(
            search=SearchVector('name', 'email', 'phone')
        ).filter(search=value)
```
