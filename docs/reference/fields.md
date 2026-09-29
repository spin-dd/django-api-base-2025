# fields

カスタムフィールドを提供するモジュールです。

## フォームフィールド

### ListCharField

カンマ区切りの文字列リストを受け入れるフィールドです。

```python
from apibase.fields import ListCharField
```

**使用例**

```python
class MyFilter(BaseFilter):
    codes = ListCharInFilter(field_name='code')
    # ListCharFieldが内部で使用される
```

---

### ListIntegerField

カンマ区切りの整数リストを受け入れるフィールドです。

```python
from apibase.fields import ListIntegerField
```

**使用例**

```python
class MyFilter(BaseFilter):
    ids = ListIntegerInFilter(field_name='id')
    # ListIntegerFieldが内部で使用される
```

---

### MonthRangeField

月単位の範囲を受け入れるフィールドです。

```python
from apibase.fields import MonthRangeField
```

**使用例**

```python
class MyFilter(BaseFilter):
    created_month = MonthFromToRangeFilter(field_name='created_at')
    # MonthRangeFieldが内部で使用される
```

---

### CharRangeField

文字列範囲を受け入れるフィールドです。

```python
from apibase.fields import CharRangeField
```

**使用例**

```python
class MyFilter(BaseFilter):
    code_range = CharRangeFilter(field_name='code')
    # CharRangeFieldが内部で使用される
```

---

## 使用例

### フィルタでの使用

```python
from apibase.filters import BaseFilter, ListCharInFilter, ListIntegerInFilter

class ProductFilter(BaseFilter):
    # ListCharFieldを使用
    categories = ListCharInFilter(field_name='category__code')

    # ListIntegerFieldを使用
    price_tiers = ListIntegerInFilter(field_name='price_tier')

    class Meta:
        model = Product
        fields = {}
```

### クエリ例

```bash
# 複数カテゴリで検索
curl "http://localhost:8000/api/products/?categories=electronics,books,toys"

# 複数価格帯で検索
curl "http://localhost:8000/api/products/?price_tiers=1,2,3"
```
