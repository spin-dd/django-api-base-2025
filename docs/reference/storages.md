# storages

ストレージ操作ユーティリティを提供するモジュールです。

## クラス

### LocalPathResolver

ローカルファイルパスからモデルインスタンスを解決するクラスです。

```python
from apibase.storages import LocalPathResolver
```

**クラスメソッド**

#### find

```python
@classmethod
def find(cls, model, field_name, path) -> Model | None
```

ファイルパスからモデルインスタンスを検索します。

**引数**

- `model` - モデルクラス
- `field_name` - FileFieldの名前
- `path` - ファイルパス

**戻り値**

- モデルインスタンス、見つからない場合はNone

**使用例**

```python
from apibase.storages import LocalPathResolver
from myapp.models import Document

# パスからDocumentインスタンスを取得
document = LocalPathResolver.find(
    Document,
    'file',
    'documents/report.pdf'
)
```

---

## 使用例

### ViewSetでの使用

```python
from apibase.viewsets import BaseModelViewSet
from apibase.storages import LocalPathResolver

class DocumentViewSet(BaseModelViewSet):
    def download_filefield_storage(self, request, field=None, name=None, format=None):
        """ストレージパスからダウンロード"""
        path = f"{name}.{format}" if format else name
        instance = LocalPathResolver.find(self.queryset.model, field, path)

        if not instance:
            raise Http404

        return self.response_field_data(request, instance, field)
```

### カスタムストレージの使用

```python
from django.core.files.storage import FileSystemStorage

custom_storage = FileSystemStorage(
    location='/path/to/files',
    base_url='/files/'
)

class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        storage=custom_storage
    )
```
