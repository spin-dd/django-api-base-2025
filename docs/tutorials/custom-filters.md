# カスタムフィルタ作成

このチュートリアルでは、独自のフィルタを作成する方法を学びます。

## ゴール

- カスタムフィルタの作成方法
- 複雑な検索条件の実装
- フィルタのテスト

## 1. 基本的なカスタムフィルタ

### 価格帯フィルタ

文字列で価格帯を指定するフィルタを作成します。

```python
# myapp/api/filters.py
import django_filters
from django.db.models import Q


class PriceRangeFilter(django_filters.CharFilter):
    """
    価格帯フィルタ
    形式: "min-max" (例: "1000-5000")
    """

    def filter(self, qs, value):
        if not value:
            return qs

        try:
            parts = value.split('-')
            if len(parts) == 2:
                min_price, max_price = parts
                if min_price:
                    qs = qs.filter(price__gte=int(min_price))
                if max_price:
                    qs = qs.filter(price__lte=int(max_price))
            elif len(parts) == 1:
                # 単一値の場合は完全一致
                qs = qs.filter(price=int(parts[0]))
        except ValueError:
            pass

        return qs
```

使用例:

```bash
# 1000円以上5000円以下
curl "http://localhost:8000/api/products/?price_range=1000-5000"

# 3000円以上
curl "http://localhost:8000/api/products/?price_range=3000-"

# 2000円以下
curl "http://localhost:8000/api/products/?price_range=-2000"
```

## 2. 複合検索フィルタ

### 住所検索フィルタ

複数フィールドを横断的に検索するフィルタ:

```python
import django_filters
from django.db.models import Q
import jaconv


class AddressSearchFilter(django_filters.CharFilter):
    """
    住所検索フィルタ
    都道府県、市区町村、番地を横断検索
    """

    def __init__(self, *args, **kwargs):
        self.address_fields = kwargs.pop('address_fields', [
            'prefecture', 'city', 'address1', 'address2'
        ])
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value:
            return qs

        # 全角・半角変換
        search_values = [
            jaconv.zen2han(value, ascii=True, digit=True),
            jaconv.han2zen(value, ascii=True, digit=True),
            value
        ]
        search_values = list(set(search_values))

        # 各フィールドでOR検索
        q = Q()
        for field in self.address_fields:
            for v in search_values:
                q |= Q(**{f'{field}__contains': v})

        return qs.filter(q).distinct() if self.distinct else qs.filter(q)
```

使用例:

```python
class CustomerFilter(BaseFilter):
    address = AddressSearchFilter(
        label='住所検索',
        address_fields=['prefecture', 'city', 'address1']
    )

    class Meta:
        model = Customer
        fields = {}
```

## 3. 日付関連フィルタ

### 相対日付フィルタ

「過去7日」「今月」などの相対日付で検索:

```python
import django_filters
from django.utils import timezone
from datetime import timedelta


class RelativeDateFilter(django_filters.CharFilter):
    """
    相対日付フィルタ
    値: today, yesterday, this_week, last_week, this_month, last_month, last_7_days, last_30_days
    """

    def filter(self, qs, value):
        if not value:
            return qs

        today = timezone.now().date()

        date_ranges = {
            'today': (today, today),
            'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
            'this_week': (today - timedelta(days=today.weekday()), today),
            'last_week': (
                today - timedelta(days=today.weekday() + 7),
                today - timedelta(days=today.weekday() + 1)
            ),
            'this_month': (today.replace(day=1), today),
            'last_month': self._get_last_month_range(today),
            'last_7_days': (today - timedelta(days=6), today),
            'last_30_days': (today - timedelta(days=29), today),
        }

        if value in date_ranges:
            start_date, end_date = date_ranges[value]
            qs = qs.filter(
                **{
                    f'{self.field_name}__gte': start_date,
                    f'{self.field_name}__lte': end_date
                }
            )

        return qs

    def _get_last_month_range(self, today):
        first_of_this_month = today.replace(day=1)
        last_of_last_month = first_of_this_month - timedelta(days=1)
        first_of_last_month = last_of_last_month.replace(day=1)
        return (first_of_last_month, last_of_last_month)
```

使用例:

```python
class OrderFilter(BaseFilter):
    created_date = RelativeDateFilter(field_name='created_at__date')

    class Meta:
        model = Order
        fields = {}
```

```bash
# 過去7日間の注文
curl "http://localhost:8000/api/orders/?created_date=last_7_days"

# 今月の注文
curl "http://localhost:8000/api/orders/?created_date=this_month"
```

## 4. ステータスフィルタ

### 複数ステータス選択フィルタ

```python
import django_filters


class MultiStatusFilter(django_filters.CharFilter):
    """
    複数ステータス選択フィルタ
    カンマ区切りで複数指定可能
    """

    def __init__(self, *args, valid_statuses=None, **kwargs):
        self.valid_statuses = valid_statuses or []
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value:
            return qs

        statuses = [s.strip() for s in value.split(',')]

        # 有効なステータスのみフィルタ
        if self.valid_statuses:
            statuses = [s for s in statuses if s in self.valid_statuses]

        if statuses:
            qs = qs.filter(**{f'{self.field_name}__in': statuses})

        return qs
```

使用例:

```python
class OrderFilter(BaseFilter):
    status = MultiStatusFilter(
        valid_statuses=['pending', 'confirmed', 'shipped', 'cancelled']
    )

    class Meta:
        model = Order
        fields = {}
```

```bash
# 処理待ちまたは確定の注文
curl "http://localhost:8000/api/orders/?status=pending,confirmed"
```

## 5. 全文検索フィルタ

### PostgreSQL全文検索

```python
import django_filters
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


class FullTextSearchFilter(django_filters.CharFilter):
    """
    PostgreSQL全文検索フィルタ
    """

    def __init__(self, *args, search_fields=None, **kwargs):
        self.search_fields = search_fields or []
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value or not self.search_fields:
            return qs

        search_vector = SearchVector(*self.search_fields)
        search_query = SearchQuery(value)

        return qs.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank')
```

## 6. フィルタのテスト

### テストケースの作成

```python
from django.test import TestCase
from .filters import PriceRangeFilter, RelativeDateFilter
from .models import Product


class PriceRangeFilterTest(TestCase):
    def setUp(self):
        Product.objects.create(name='Product 1', price=1000)
        Product.objects.create(name='Product 2', price=2000)
        Product.objects.create(name='Product 3', price=3000)

    def test_min_max_range(self):
        filter = PriceRangeFilter(field_name='price')
        qs = Product.objects.all()

        result = filter.filter(qs, '1500-2500')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Product 2')

    def test_min_only(self):
        filter = PriceRangeFilter(field_name='price')
        qs = Product.objects.all()

        result = filter.filter(qs, '2000-')
        self.assertEqual(result.count(), 2)

    def test_max_only(self):
        filter = PriceRangeFilter(field_name='price')
        qs = Product.objects.all()

        result = filter.filter(qs, '-2000')
        self.assertEqual(result.count(), 2)

    def test_empty_value(self):
        filter = PriceRangeFilter(field_name='price')
        qs = Product.objects.all()

        result = filter.filter(qs, '')
        self.assertEqual(result.count(), 3)


class RelativeDateFilterTest(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone

        today = timezone.now()
        Order.objects.create(created_at=today)
        Order.objects.create(created_at=today - timedelta(days=1))
        Order.objects.create(created_at=today - timedelta(days=7))
        Order.objects.create(created_at=today - timedelta(days=30))

    def test_today(self):
        filter = RelativeDateFilter(field_name='created_at__date')
        qs = Order.objects.all()

        result = filter.filter(qs, 'today')
        self.assertEqual(result.count(), 1)

    def test_last_7_days(self):
        filter = RelativeDateFilter(field_name='created_at__date')
        qs = Order.objects.all()

        result = filter.filter(qs, 'last_7_days')
        self.assertEqual(result.count(), 3)
```

## 7. フィルタの登録

### FilterSetへの追加

```python
from apibase.filters import BaseFilter
from .custom_filters import PriceRangeFilter, RelativeDateFilter, MultiStatusFilter


class ProductFilter(BaseFilter):
    price_range = PriceRangeFilter(field_name='price')

    class Meta:
        model = Product
        fields = {
            'name': ['contains'],
            'category': ['exact'],
        }


class OrderFilter(BaseFilter):
    created_date = RelativeDateFilter(field_name='created_at__date')
    status = MultiStatusFilter(
        valid_statuses=['pending', 'confirmed', 'shipped', 'cancelled']
    )

    class Meta:
        model = Order
        fields = {}
```

## 次のステップ

- [フィルタリング機能ガイド](../guides/filters.md)
- [日本語検索の実例](../examples/word-filter.md)
