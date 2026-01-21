# ファイルダウンロード

apibaseは、FileFieldからのダウンロード機能を提供します。

## 概要

`DownloadMixin`を使用すると、以下のエンドポイントが自動的に追加されます:

- 単一レコードのFileFieldダウンロード
- ストレージパスからの直接ダウンロード

## 基本的な使い方

### ViewSetの設定

```python
from apibase.viewsets import BaseModelViewSet
from .models import Document

class DocumentViewSet(BaseModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
```

`BaseModelViewSet`には`DownloadMixin`が含まれているため、追加設定なしでダウンロード機能が使えます。

### モデル例

```python
from django.db import models

class Document(models.Model):
    title = models.CharField('タイトル', max_length=200)
    file = models.FileField('ファイル', upload_to='documents/')
    attachment = models.FileField('添付', upload_to='attachments/', blank=True)

    def __str__(self):
        return self.title
```

## エンドポイント

### 単一レコードからのダウンロード

```
GET /api/documents/{id}/{field_name}/download/
```

例:

```bash
# file フィールドをダウンロード
curl -O "http://localhost:8000/api/documents/1/file/download/"

# attachment フィールドをダウンロード
curl -O "http://localhost:8000/api/documents/1/attachment/download/"
```

### ストレージパスからのダウンロード

```
GET /api/documents/storage/{field_name}/{file_path}
```

例:

```bash
curl -O "http://localhost:8000/api/documents/storage/file/documents/report.pdf"
```

## ファイル名のカスタマイズ

### デフォルトのファイル名

デフォルトでは、ファイル名は以下の形式になります:

```
{field.verbose_name}.{str(instance)}{extension}
```

例: `ファイル.報告書2024.pdf`

### カスタムファイル名

`get_download_filefield_name`メソッドをオーバーライド:

```python
class DocumentViewSet(BaseModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_download_filefield_name(self, instance, field):
        """ダウンロードファイル名を生成"""
        from pathlib import Path
        ext = Path(field.path).suffix
        return f"{instance.title}_{instance.created_at.strftime('%Y%m%d')}{ext}"
```

## レスポンスのカスタマイズ

### create_download_filefield_response

レスポンスをカスタマイズする場合:

```python
from django.http import FileResponse

class DocumentViewSet(BaseModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def create_download_filefield_response(self, request, instance, field, format=None):
        """カスタムレスポンスを生成"""
        response = FileResponse(
            field.open('rb'),
            content_type='application/octet-stream'
        )
        return response
```

### ストリーミングレスポンス

大きなファイルの場合:

```python
from django.http import StreamingHttpResponse

def create_download_filefield_response(self, request, instance, field, format=None):
    def file_iterator(file_path, chunk_size=8192):
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                yield chunk

    response = StreamingHttpResponse(
        file_iterator(field.path),
        content_type='application/octet-stream'
    )
    return response
```

## Content-Disposition

レスポンスには自動的に`Content-Disposition`ヘッダーが設定されます:

```python
from apibase.utils import to_content_disposition

# 日本語ファイル名も正しくエンコード
header = to_content_disposition("報告書2024.pdf")
# Content-Disposition: attachment; filename*=UTF-8''%E5%A0%B1%E5%91%8A%E6%9B%B82024.pdf
```

## ストレージ

### LocalPathResolver

ストレージパスからモデルインスタンスを解決:

```python
from apibase.storages import LocalPathResolver

# パスからインスタンスを取得
instance = LocalPathResolver.find(
    Document,      # モデルクラス
    'file',        # フィールド名
    'documents/report.pdf'  # パス
)
```

## 静的ファイルサーブ

### static_serve

認証なしで静的ファイルを配信:

```python
from apibase.viewsets import static_serve

urlpatterns = [
    path('media/<path:path>', static_serve, {'document_root': settings.MEDIA_ROOT}),
]
```

### ダウンロード名付き

```python
def download_view(request, path):
    return static_serve(
        request,
        path,
        name='download.pdf',  # ダウンロードファイル名
        document_root=settings.MEDIA_ROOT
    )
```

## セキュリティ

### 認証の確認

```python
from rest_framework.permissions import IsAuthenticated

class DocumentViewSet(BaseModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
```

### オブジェクトレベルの権限

```python
class DocumentViewSet(BaseModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_object(self):
        obj = super().get_object()
        if not obj.can_download(self.request.user):
            raise PermissionDenied()
        return obj
```

### ダウンロード制限

```python
from django.core.cache import cache
from rest_framework.exceptions import Throttled

class DocumentViewSet(BaseModelViewSet):
    def download_filefield(self, request, pk, format=None, field=None):
        user_id = request.user.id
        cache_key = f'download_count_{user_id}'
        count = cache.get(cache_key, 0)

        if count >= 100:  # 1日100回まで
            raise Throttled(detail='Download limit exceeded')

        cache.set(cache_key, count + 1, timeout=86400)
        return super().download_filefield(request, pk, format, field)
```

## 次のステップ

- [ファイルアップロード/ダウンロードの実例](../examples/file-upload-download.md)
- [ストレージAPIリファレンス](../reference/storages.md)
