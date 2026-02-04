# archives

アーカイブ機能を提供するモジュールです。

## 概要

ファイルのアーカイブ（ZIP等）作成機能を提供します。

## 使用例

### 複数ファイルのZIPアーカイブ

```python
import zipfile
from io import BytesIO
from django.http import HttpResponse

def download_zip(request, pk):
    """複数ファイルをZIPでダウンロード"""
    order = Order.objects.get(pk=pk)
    documents = order.documents.all()

    # ZIPファイルを作成
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in documents:
            zf.writestr(doc.filename, doc.file.read())

    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="order_{pk}_documents.zip"'
    return response
```

### ViewSetでのZIPダウンロード

```python
from rest_framework.decorators import action
from rest_framework.response import Response
import zipfile
from io import BytesIO
from django.http import HttpResponse

class OrderViewSet(BaseModelViewSet):
    @action(detail=True, methods=['get'])
    def download_all(self, request, pk=None):
        """全添付ファイルをZIPでダウンロード"""
        order = self.get_object()

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in order.items.all():
                if item.attachment:
                    zf.writestr(
                        f"{item.product.name}_{item.id}.pdf",
                        item.attachment.read()
                    )

        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="order_{pk}_files.zip"'
        return response
```
