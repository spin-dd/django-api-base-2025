# renderers

レンダラークラスを提供するモジュールです。

## 概要

apibaseはDjango REST Frameworkの標準レンダラーを使用し、追加でCSVレンダラーをサポートします。

## サポートされるレンダラー

### JSONRenderer

```python
from rest_framework.renderers import JSONRenderer
```

デフォルトのJSONレンダラー。

### BrowsableAPIRenderer

```python
from rest_framework.renderers import BrowsableAPIRenderer
```

ブラウザで閲覧可能なAPIインターフェース。

### CSVRenderer

```python
from rest_framework_csv.renderers import CSVRenderer
```

CSV形式でのエクスポート。

---

## 設定

### REST_FRAMEWORK設定

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ],
}
```

---

## CSVエクスポート

### ViewSetの設定

```python
from apibase.viewsets import BaseModelViewSet

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    fields_query = 'fields'  # フィールド指定用クエリパラメータ
```

### リクエスト例

```bash
# CSV形式でエクスポート
curl -H "Accept: text/csv" \
  "http://localhost:8000/api/products/"

# フィールドを指定してエクスポート
curl -H "Accept: text/csv" \
  "http://localhost:8000/api/products/?fields=id,name,price"
```

### レスポンス例

```csv
id,name,price
1,Product 1,1000
2,Product 2,2000
```

---

## ラベルのカスタマイズ

シリアライザでフィールドにラベルを設定すると、CSVヘッダーに反映されます。

```python
class ProductSerializer(BaseModelSerializer):
    id = serializers.IntegerField(label='ID')
    name = serializers.CharField(label='商品名')
    price = serializers.IntegerField(label='価格')

    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
```

レスポンス:

```csv
ID,商品名,価格
1,Product 1,1000
2,Product 2,2000
```

---

## エンコーディング

### UTF-8 with BOM

日本語を含むCSVをExcelで正しく開くため、`get_renderer_context`でUTF-8 BOMエンコーディングを設定:

```python
class ProductViewSet(BaseModelViewSet):
    def get_renderer_context(self):
        context = super().get_renderer_context()
        if self.request.META.get("HTTP_ACCEPT", "").startswith("text/csv"):
            context["encoding"] = "utf-8-sig"  # BOM付きUTF-8
        return context
```

---

## カスタムレンダラー

```python
from rest_framework.renderers import BaseRenderer

class PlainTextRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return str(data).encode('utf-8')

class ProductViewSet(BaseModelViewSet):
    renderer_classes = [JSONRenderer, PlainTextRenderer]
```
