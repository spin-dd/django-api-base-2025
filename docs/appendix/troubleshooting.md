# トラブルシューティング

よくある問題と解決方法です。

## インストール関連

### ImportError: No module named 'apibase'

**原因**: パッケージがインストールされていない

**解決策**:

```bash
pip install apibase
```

### ModuleNotFoundError: No module named 'rest_framework'

**原因**: Django REST Frameworkがインストールされていない

**解決策**:

```bash
pip install djangorestframework
```

## 設定関連

### ImproperlyConfigured: You must define 'INSTALLED_APPS'

**原因**: Django設定が正しくない

**解決策**: `settings.py`に以下を追加:

```python
INSTALLED_APPS = [
    'rest_framework',
    'django_filters',
    # ...
]
```

### RuntimeError: settings.DATABASES is improperly configured

**原因**: データベース設定がない

**解決策**: `settings.py`にデータベース設定を追加

## ViewSet関連

### AttributeError: 'NoneType' object has no attribute 'split'

**原因**: `pagination_class`が正しく設定されていない

**解決策**:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
    'PAGE_SIZE': 20,
}
```

### PermissionDenied: Authentication credentials were not provided

**原因**: 認証が必要なエンドポイントに未認証でアクセス

**解決策**: 認証情報を提供するか、権限設定を確認

```python
class ProductViewSet(BaseModelViewSet):
    permission_classes = [AllowAny]  # 認証不要にする場合
```

## Serializer関連

### Field name 'endpoint' is not valid for model

**原因**: `endpoint`フィールドがモデルに存在しない

**解決策**: `endpoint`は`BaseModelSerializer`が自動的に提供するため、`Meta.fields`に含めるだけでOK

```python
class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'endpoint', 'urn', 'display']
```

### Serializer field validation error

**原因**: バリデーションエラー

**解決策**: エラーメッセージを確認し、データを修正

```json
{
    "name": ["この項目は必須です。"],
    "price": ["この項目は正の整数である必要があります。"]
}
```

## Filter関連

### FilterError: No field found with name 'xxx'

**原因**: フィルタフィールドがモデルに存在しない

**解決策**: フィールド名を確認

```python
class ProductFilter(BaseFilter):
    class Meta:
        model = Product
        fields = {'name': ['exact']}  # 'name'がモデルに存在するか確認
```

### WordFilterが動作しない

**原因**: `lookups`が設定されていない

**解決策**:

```python
search = WordFilter(
    lookups=['name', 'description'],  # 必ず設定
)
```

## GraphQL関連

### GraphQLError: Cannot query field 'xxx'

**原因**: スキーマにフィールドが定義されていない

**解決策**: 型定義を確認

```python
class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = ['id', 'title', 'xxx']  # xxxを追加
```

### N+1クエリの問題

**原因**: 関連データの取得が最適化されていない

**解決策**: `select_related`/`prefetch_related`を使用

```python
def resolve_books(self, info):
    return Book.objects.select_related('author').all()
```

## ファイルダウンロード関連

### Http404: ファイルが見つからない

**原因**: ファイルが存在しない、またはパスが間違っている

**解決策**:

1. ファイルが存在するか確認
2. `MEDIA_ROOT`の設定を確認
3. ファイルパスを確認

### ファイル名が文字化け

**原因**: Content-Dispositionのエンコーディング問題

**解決策**: `to_content_disposition`関数を使用

```python
from apibase.utils import to_content_disposition

response['Content-Disposition'] = to_content_disposition(filename)
```

## パフォーマンス関連

### クエリが遅い

**解決策**:

1. インデックスを追加
2. `select_related`/`prefetch_related`を使用
3. クエリセットを最適化

```python
class ProductViewSet(BaseModelViewSet):
    def get_queryset(self):
        return Product.objects.select_related('category').all()
```

### メモリ不足

**解決策**:

1. ページサイズを小さくする
2. `iterator()`を使用
3. ストリーミングレスポンスを使用

## デバッグ方法

### Djangoデバッグツールバー

```bash
pip install django-debug-toolbar
```

### SQLクエリの確認

```python
from django.db import connection

# クエリ実行後
print(connection.queries)
```

### ログの有効化

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```
