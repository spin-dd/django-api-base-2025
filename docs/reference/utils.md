# utils

汎用ユーティリティ関数を提供するモジュールです。

## 関数

### to_content_disposition

```python
def to_content_disposition(filename: str) -> str
```

ファイル名からContent-Dispositionヘッダー値を生成します。

**引数**

- `filename` - ファイル名

**戻り値**

- `str` - Content-Dispositionヘッダー値

**動作**

- 日本語などの非ASCII文字を適切にエンコード
- RFC 5987に準拠した形式を生成

**使用例**

```python
from apibase.utils import to_content_disposition

header = to_content_disposition("報告書2024.pdf")
# "attachment; filename*=UTF-8''%E5%A0%B1%E5%91%8A%E6%9B%B82024.pdf"
```

---

## 使用例

### ファイルダウンロードでの使用

```python
from django.http import FileResponse
from apibase.utils import to_content_disposition

def download_view(request, pk):
    document = Document.objects.get(pk=pk)
    response = FileResponse(document.file)
    response['Content-Disposition'] = to_content_disposition(document.filename)
    return response
```

### ViewSetでの使用

```python
from apibase.viewsets import BaseModelViewSet
from apibase.utils import to_content_disposition

class DocumentViewSet(BaseModelViewSet):
    def create_download_filefield_response(self, request, instance, field, format=None):
        response = super().create_download_filefield_response(request, instance, field, format)
        response['Content-Disposition'] = to_content_disposition(f"{instance.title}.pdf")
        return response
```
