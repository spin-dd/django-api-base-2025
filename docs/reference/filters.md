# filters

フィルタクラスを提供するモジュールです。

## クラス

### BaseFilter

すべてのフィルタセットの基底クラスです。

```python
from apibase.filters import BaseFilter
```

**継承元**

- `django_filters.FilterSet`

**組み込みフィルタ**

| フィルタ名 | 型 | 説明 |
|-----------|-----|------|
| `pk` | `NumberFilter` | 主キーで検索 |
| `id__includes` | `ListIntegerInFilter` | IDを含む（CSV形式） |
| `id__excludes` | `ListIntegerInFilter` | IDを除外（CSV形式） |
| `id__in_csv` | `BaseInFilter` | IDを含む（CSV形式） |
| `id__not_in_csv` | `BaseInFilter` | IDを除外（CSV形式） |

**クラスメソッド**

#### filter_for_lookup

```python
@classmethod
def filter_for_lookup(cls, field, lookup_type)
```

フィールドとルックアップタイプに対応するフィルタクラスを返します。IntegerFieldのChoiceFilterをIntFilterに変換します。

---

### FanOutBaseFilter

M2M・reverse FK の自動生成フィルターを、外側の `DISTINCT` ではなく主キーの非相関
サブクエリで畳む opt-in の FilterSet 基底です。通常の `BaseFilter` の既定は変えません。

```python
from apibase.filters import FanOutBaseFilter
```

明示宣言用のクラス:

- `FanOutCharFilter`
- `FanOutWordFilter`
- `FanOutModelChoiceFilter`
- `FanOutModelMultipleChoiceFilter`
- `FanOutDateFromToRangeFilter`

これらは `folds_fan_out=True` を公開し、GraphQL の distinct 判定にも畳み込み済みであることを
伝えます。空入力と空の複数選択は queryset を変更しません。

---

### WordFilter

日本語検索に対応したフィルタです。

```python
from apibase.filters import WordFilter
```

**継承元**

- `django_filters.CharFilter`

**引数**

| 引数 | 型 | デフォルト | 説明 |
|-----|-----|----------|------|
| `lookups` | `list[str]` | `[]` | 検索対象フィールドのリスト |
| `delimiters` | `str` | `r"[\s\u3000,]+"` | 区切り文字の正規表現 |
| `lookup_expr` | `str` | `"contains"` | ルックアップ式 |

**動作**

1. 入力値を区切り文字で分割
2. 各単語を全角/半角両方で検索
3. 複数単語はAND条件
4. 各フィールドはOR条件

**使用例**

```python
class CustomerFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['name', 'email', 'phone'],
    )
```

---

### ListCharInFilter

カンマ区切り文字列リストでIN検索を行うフィルタです。

```python
from apibase.filters import ListCharInFilter
```

**使用例**

```python
class ProductFilter(BaseFilter):
    codes = ListCharInFilter(field_name='code')
```

```
?codes=A001,A002,A003
```

---

### ListIntegerInFilter

カンマ区切り整数リストでIN検索を行うフィルタです。

```python
from apibase.filters import ListIntegerInFilter
```

**使用例**

```python
class ProductFilter(BaseFilter):
    category_ids = ListIntegerInFilter(field_name='category_id')
```

---

### MonthFromToRangeFilter

月単位の範囲フィルタです。

```python
from apibase.filters import MonthFromToRangeFilter
```

**使用例**

```python
class OrderFilter(BaseFilter):
    created_month = MonthFromToRangeFilter(field_name='created_at')
```

```
?created_month_after=2024-01&created_month_before=2024-03
```

---

### CharRangeFilter

文字列範囲フィルタです。

```python
from apibase.filters import CharRangeFilter
```

**使用例**

```python
class ProductFilter(BaseFilter):
    code_range = CharRangeFilter(field_name='code')
```

```
?code_range_min=A100&code_range_max=A200
```

---

### AllValuesMultipleFilter

モデルに存在する値のみを選択肢とする複数選択フィルタです。

```python
from apibase.filters import AllValuesMultipleFilter
```

**継承元**

- `django_filters.AllValuesMultipleFilter`

---

### IntFilter

整数用フィルタです。

```python
from apibase.filters import IntFilter
```

**継承元**

- `django_filters.NumberFilter`

---

### RelatedFilterSetMixin

関連フィルタセットを作成するためのミックスインです。

```python
from apibase.filters import RelatedFilterSetMixin
```

**クラスメソッド**

#### create_related_filterset

```python
@classmethod
def create_related_filterset(cls, related_name, fields=None, exclude=None, methods="keep") -> type
```

関連名を指定して関連フィルタセットを作成します。`fields` / `exclude` / `methods` は
`clone_filter_fields` にそのまま渡ります。

---

## 関数

### clone_filter_fields

```python
def clone_filter_fields(
    filter_class, prefix, distinct=None, fields=None, exclude=None, methods="keep"
) -> dict
```

フィルタセットのフィールドを複製し、プレフィックスを追加します。

**引数**

- `filter_class` - 複製元のフィルタクラス
- `prefix` - フィールド名のプレフィックス
- `distinct` - distinctの設定
- `fields` - 複製するフィールド（Noneで全て）。名前は**複製元のフィルタキー**（プレフィックス前）
- `exclude` - 除外するフィールド。`fields` との同時指定は `TypeError`
- `methods` - 文字列 `method` を持つフィルタの扱い。`"keep"`（既定・複製する） / `"drop"`（複製しない） / `"error"`（複製を拒否して `ValueError`）

`fields` / `exclude` に存在しない名前を渡すと `ValueError`。typo が黙って全件複製（`fields`）や
無効化（`exclude`）にならないようにするためです。

**戻り値**

- `dict` - プレフィックス付きフィルタフィールドの辞書

**使用例**

```python
# AuthorFilterのフィールドをauthor__プレフィックス付きで複製
filters = clone_filter_fields(AuthorFilter, 'author')
BookFilter.base_filters.update(filters)
```

---

### make_related_filterset

```python
def make_related_filterset(
    type_name, distinct=True, base_filters=None, methods="keep", **related_filters
) -> type
```

関連フィルタセットを動的に生成します。

**引数**

- `type_name` - 生成するクラス名
- `distinct` - distinctの設定
- `base_filters` - 基底フィルタクラスのタプル
- `methods` - 文字列 `method` を持つフィルタの扱い（`clone_filter_fields` と同じ）
- `**related_filters` - 関連名とフィルタクラスのマッピング

**戻り値**

- 生成されたフィルタセットクラス

**使用例**

```python
BookWithRelationsFilter = make_related_filterset(
    'BookWithRelationsFilter',
    author=AuthorFilter,
    publisher=PublisherFilter,
)
```

---

### validate_method_filters

```python
def validate_method_filters(filter_class) -> list[tuple[str, str]]
```

`filter_class` が解決できない文字列 `method` を `(フィルタキー, メソッド名)` で返します。
django-filter は文字列 `method` を**クエリ実行時**に親フィルタセットから引くため、解決できない
名前は import では気付けず、そのクエリパラメータを最初に使ったリクエストで `AssertionError`
になります。複製で組み立てたフィルタセットは、自分のテストで空を assert してください。

**使用例**

```python
from apibase.filters import validate_method_filters

def test_filtersets_can_resolve_their_methods():
    assert validate_method_filters(BookWithAuthorFilter) == []
```

---

## 使用例

### 基本的なフィルタセット

```python
from apibase.filters import BaseFilter, WordFilter

class ProductFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['name', 'description'],
    )

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'contains'],
            'category': ['exact'],
            'price': ['exact', 'gte', 'lte'],
        }
```

### 関連フィルタの統合

```python
from apibase.filters import BaseFilter, clone_filter_fields

class AuthorFilter(BaseFilter):
    class Meta:
        model = Author
        fields = {'name': ['contains']}

class BookFilter(BaseFilter):
    class Meta:
        model = Book
        fields = {'title': ['contains']}

# 著者フィルタを統合
BookFilter.base_filters.update(
    clone_filter_fields(AuthorFilter, 'author')
)
```
