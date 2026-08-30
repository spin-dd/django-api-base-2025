# ファイルアップロード/ダウンロード

ファイル操作の実装例です。

## モデル

```python
# documents/models.py
from django.db import models

class Document(models.Model):
    title = models.CharField('タイトル', max_length=200)
    file = models.FileField('ファイル', upload_to='documents/')
    thumbnail = models.ImageField('サムネイル', upload_to='thumbnails/', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    def __str__(self):
        return self.title
```

## シリアライザ

```python
# documents/api/serializers.py
from rest_framework import serializers
from apibase.serializers import BaseModelSerializer
from ..models import Document

class DocumentSerializer(BaseModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file', 'file_url', 'file_size',
            'thumbnail', 'created_at',
            'endpoint', 'urn', 'display'
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return 0
```

## ViewSet

```python
# documents/api/viewsets.py
from pathlib import Path
from apibase.viewsets import BaseModelViewSet
from apibase.utils import to_content_disposition
from ..models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(BaseModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_download_filefield_name(self, instance, field):
        """カスタムダウンロードファイル名"""
        ext = Path(field.path).suffix
        return f"{instance.title}{ext}"
```

## ファイルアップロード

### multipart/form-data

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -F "title=報告書" \
  -F "file=@/path/to/report.pdf"
```

### Base64エンコード

```python
# serializer
class DocumentSerializer(BaseModelSerializer):
    file_base64 = serializers.CharField(write_only=True, required=False)

    def create(self, validated_data):
        file_base64 = validated_data.pop('file_base64', None)
        if file_base64:
            import base64
            from django.core.files.base import ContentFile

            format, data = file_base64.split(';base64,')
            ext = format.split('/')[-1]
            validated_data['file'] = ContentFile(
                base64.b64decode(data),
                name=f"upload.{ext}"
            )
        return super().create(validated_data)
```

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "報告書",
    "file_base64": "data:application/pdf;base64,JVBERi0xLjQK..."
  }'
```

## ファイルダウンロード

### FileFieldダウンロード

```bash
# 直接ダウンロード
curl -O http://localhost:8000/api/documents/1/file/download/

# サムネイルダウンロード
curl -O http://localhost:8000/api/documents/1/thumbnail/download/
```

### ストレージパスからダウンロード

```bash
curl -O http://localhost:8000/api/documents/storage/file/documents/report.pdf
```

## 複数ファイルのZIPダウンロード

```python
# viewsets.py
import zipfile
from io import BytesIO
from django.http import HttpResponse
from rest_framework.decorators import action

class DocumentViewSet(BaseModelViewSet):
    @action(detail=False, methods=['get'])
    def download_all(self, request):
        """全ファイルをZIPでダウンロード"""
        buffer = BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for doc in self.get_queryset():
                if doc.file:
                    zf.writestr(
                        f"{doc.title}{Path(doc.file.name).suffix}",
                        doc.file.read()
                    )

        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="documents.zip"'
        return response
```

## 大きなファイルのストリーミング

```python
from django.http import StreamingHttpResponse

class DocumentViewSet(BaseModelViewSet):
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
