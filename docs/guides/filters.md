# フィルタリング機能

apibaseは、django-filterを拡張した高度なフィルタリング機能を提供します。

## BaseFilter

すべてのフィルタセットのベースクラスです:

```python
from apibase.filters import BaseFilter
from .models import Product

class ProductFilter(BaseFilter):
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'category': ['exact'],
        }
```

### 組み込みフィルタ

`BaseFilter`には以下のフィルタが組み込まれています:

| フィルタ名 | 説明 | 例 |
|-----------|------|-----|
| `pk` | 主キーで検索 | `?pk=1` |
| `id__includes` | 複数IDを含む | `?id__includes=1,2,3` |
| `id__excludes` | 複数IDを除外 | `?id__excludes=4,5` |
| `id__in_csv` | CSVフォーマットでIDを指定 | `?id__in_csv=1,2,3` |
| `id__not_in_csv` | CSVフォーマットで除外 | `?id__not_in_csv=4,5` |

## WordFilter

日本語検索に対応したフィルタです。全角・半角を自動的に変換して検索します。

```python
from apibase.filters import BaseFilter, WordFilter
from .models import Customer

class CustomerFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['name', 'email', 'phone'],
    )

    class Meta:
        model = Customer
        fields = {}
```

### 動作

- スペース区切りで複数キーワードをAND検索
- 全角・半角カタカナを両方で検索
- 全角・半角英数字を両方で検索

```bash
# "山田 東京" で検索
# → name/email/phoneに「山田」AND「東京」を含む
curl "http://localhost:8000/api/customers/?search=山田 東京"
```

### オプション

```python
WordFilter(
    label='検索',
    lookups=['name', 'email'],
    lookup_expr='icontains',  # 大文字小文字無視 (デフォルト: contains)
    delimiters=r'[\s\u3000,]+',  # 区切り文字の正規表現
)
```

## ListCharInFilter / ListIntegerInFilter

カンマ区切りのリストでIN検索を行います:

```python
from apibase.filters import BaseFilter, ListCharInFilter, ListIntegerInFilter

class ProductFilter(BaseFilter):
    categories = ListCharInFilter(field_name='category__code')
    prices = ListIntegerInFilter(field_name='price')

    class Meta:
        model = Product
        fields = {}
```

使用例:

```bash
# カテゴリコードでフィルタ
curl "http://localhost:8000/api/products/?categories=electronics,books"

# 価格でフィルタ
curl "http://localhost:8000/api/products/?prices=100,200,300"
```

## 範囲フィルタ

### MonthFromToRangeFilter

月単位の範囲フィルタ:

```python
from apibase.filters import BaseFilter, MonthFromToRangeFilter

class OrderFilter(BaseFilter):
    order_date = MonthFromToRangeFilter(field_name='created_at')

    class Meta:
        model = Order
        fields = {}
```

```bash
# 2024年1月から3月の注文
curl "http://localhost:8000/api/orders/?order_date_after=2024-01&order_date_before=2024-03"
```

### CharRangeFilter

文字列の範囲フィルタ:

```python
from apibase.filters import BaseFilter, CharRangeFilter

class ProductFilter(BaseFilter):
    code_range = CharRangeFilter(field_name='code')

    class Meta:
        model = Product
        fields = {}
```

```bash
# コードがA100からA200の範囲
curl "http://localhost:8000/api/products/?code_range_min=A100&code_range_max=A200"
```

## AllValuesMultipleFilter

モデルに存在する値のみを選択肢として表示する複数選択フィルタ:

```python
from apibase.filters import BaseFilter, AllValuesMultipleFilter

class ProductFilter(BaseFilter):
    category = AllValuesMultipleFilter(field_name='category')

    class Meta:
        model = Product
        fields = {}
```

## 関連フィルタ

### clone_filter_fields

既存のフィルタセットを関連フィールド用に複製:

```python
from apibase.filters import BaseFilter, clone_filter_fields

class AuthorFilter(BaseFilter):
    name = WordFilter(lookups=['name'])

    class Meta:
        model = Author
        fields = {'country': ['exact']}

class BookFilter(BaseFilter):
    class Meta:
        model = Book
        fields = {'title': ['contains']}

# AuthorFilterのフィールドをauthor__プレフィックス付きで追加
BookFilter.base_filters.update(
    clone_filter_fields(AuthorFilter, 'author')
)
```

結果:

```bash
# 著者名で検索
curl "http://localhost:8000/api/books/?author__name=山田"

# 著者の国で検索
curl "http://localhost:8000/api/books/?author__country=JP"
```

### make_related_filterset

関連フィルタセットを動的に生成:

```python
from apibase.filters import make_related_filterset

BookWithAuthorFilter = make_related_filterset(
    'BookWithAuthorFilter',
    distinct=True,
    author=AuthorFilter,
    publisher=PublisherFilter,
)
```

### RelatedFilterSetMixin

フィルタセットから関連フィルタを生成:

```python
from apibase.filters import BaseFilter, RelatedFilterSetMixin

class AuthorFilter(RelatedFilterSetMixin, BaseFilter):
    class Meta:
        model = Author
        fields = {'name': ['contains']}

# 関連フィルタセットを作成
RelatedAuthorFilter = AuthorFilter.create_related_filterset('author')
```

## IntFilter

整数フィールド用のフィルタ（ChoiceFieldでも整数として扱う）:

```python
from apibase.filters import BaseFilter, IntFilter

class ProductFilter(BaseFilter):
    status = IntFilter(field_name='status')

    class Meta:
        model = Product
        fields = {}
```

## カスタムフィルタの作成

```python
import django_filters
from django.db.models import Q

class PriceRangeFilter(django_filters.CharFilter):
    """価格帯フィルタ (例: "1000-5000")"""

    def filter(self, qs, value):
        if not value:
            return qs

        try:
            min_price, max_price = value.split('-')
            return qs.filter(
                Q(price__gte=int(min_price)) &
                Q(price__lte=int(max_price))
            )
        except ValueError:
            return qs
```

## 次のステップ

- [カスタムフィルタ作成チュートリアル](../tutorials/custom-filters.md)
- [日本語検索の実例](../examples/word-filter.md)
