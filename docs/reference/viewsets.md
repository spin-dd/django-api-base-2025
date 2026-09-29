# viewsets

ViewSet拡張クラスを提供するモジュールです。

## クラス

### BaseModelViewSet

`rest_framework.viewsets.ModelViewSet`を拡張した基底クラスです。

```python
from apibase.viewsets import BaseModelViewSet
```

**継承元**

- `viewsets.ModelViewSet`
- `ViewSetMixin`
- `DownloadMixin`

**属性**

| 属性 | 型 | 説明 |
|-----|-----|------|
| `pagination_class` | `class` | デフォルトで`paginations.Pagination` |
| `fields_query` | `str` | CSVエクスポート用のクエリパラメータ名 |

**メソッド**

#### batch_create

```python
@action(methods=["post"], detail=False)
def batch_create(self, request, *args, **kwargs)
```

複数レコードを一括作成します。

**引数**

- `request` - リクエストオブジェクト（bodyにリスト形式のデータ）

**戻り値**

- `Response` - 作成されたオブジェクトのリスト

#### batch_update

```python
@action(methods=["patch", "get"], detail=False)
def batch_update(self, request)
```

複数レコードを一括更新します。

**引数**

- `request` - リクエストオブジェクト（bodyにリスト形式のデータ、各要素にid必須）

**戻り値**

- `Response` - 更新されたオブジェクトのリスト

---

### ViewSetMixin

ViewSetにユーティリティメソッドを追加するミックスインです。

```python
from apibase.viewsets import ViewSetMixin
```

**クラスメソッド**

#### permissions

```python
@classmethod
def permissions(cls)
```

ViewSetに関連付けられたDjango Permissionオブジェクトのリストを取得します。

**戻り値**

- `list[Permission]` - Permissionオブジェクトのリスト

**プロパティ**

#### is_safe_method

```python
@property
def is_safe_method(self) -> bool
```

現在のリクエストが安全なメソッド（GET, HEAD, OPTIONS）かどうかを返します。

---

### DownloadMixin

FileFieldのダウンロード機能を追加するミックスインです。

```python
from apibase.viewsets import DownloadMixin
```

**メソッド**

#### download_filefield

```python
@action(methods=["get"], detail=True, url_path="(?P<field>[^/.]+)/download")
def download_filefield(self, request, pk, format=None, field=None)
```

指定されたFileFieldをダウンロードします。

**URL**

```
GET /{prefix}/{pk}/{field}/download/
```

#### download_filefield_storage

```python
@action(methods=["get"], detail=False, url_path=rf"{STORAGE_PREFIX}/?(?P<field>[^/\d]+)/(?P<name>.+)")
def download_filefield_storage(self, request, field=None, name=None, format=None)
```

ストレージパスからファイルをダウンロードします。

**URL**

```
GET /{prefix}/storage/{field}/{name}
```

#### get_download_filefield_name

```python
def get_download_filefield_name(self, instance, field) -> str
```

ダウンロードファイル名を生成します。オーバーライドしてカスタマイズ可能。

**引数**

- `instance` - モデルインスタンス
- `field` - FileFieldインスタンス

**戻り値**

- `str` - ファイル名

#### create_download_filefield_response

```python
def create_download_filefield_response(self, request, instance, field, format=None)
```

ダウンロードレスポンスを生成します。オーバーライドしてカスタマイズ可能。

---

## 関数

### static_serve

```python
def static_serve(request, path, name=None, document_root="/")
```

静的ファイルを配信します。

**引数**

- `request` - リクエストオブジェクト
- `path` - ファイルパス
- `name` - ダウンロードファイル名（オプション）
- `document_root` - ドキュメントルート

**戻り値**

- `HttpResponse` - ファイルレスポンス

## 使用例

```python
from apibase.viewsets import BaseModelViewSet
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    fields_query = 'fields'  # CSV出力用

    def get_download_filefield_name(self, instance, field):
        # カスタムファイル名
        return f"{instance.name}_{field.field.name}.pdf"
```
