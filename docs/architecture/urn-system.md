# URNシステム

apibaseのURN（Uniform Resource Name）システムについて説明します。

## 概要

URNは、リソースを永続的に識別するための識別子です。URLとは異なり、リソースの場所ではなくリソース自体を識別します。

## URNの形式

```
urn:{nid}:{nss}:{identifier}
```

| 部分 | 説明 | 例 |
|------|------|-----|
| `urn` | URNスキーム | `urn` |
| `nid` | Namespace Identifier | `products` |
| `nss` | Namespace Specific String | `product` |
| `identifier` | リソース識別子 | `123` |

**例**: `urn:products:product:123`

## 設計思想

### 1. 永続性

URNはリソースの永続的な識別子として設計されています。URLが変更されても、URNは変わりません。

```python
# URLは変わる可能性がある
"/api/v1/products/123/"
"/api/v2/products/123/"

# URNは変わらない
"urn:products:product:123"
```

### 2. グローバル一意性

URNはシステム全体でユニークです。

```python
# 異なるモデルは異なるURN
"urn:products:product:1"
"urn:orders:order:1"
```

### 3. 自己記述性

URNからリソースの種類がわかります。

```python
# app_label と model_name が含まれる
"urn:products:product:123"
#     ^^^^^^^^ app_label
#              ^^^^^^^ model_name
#                      ^^^ primary key
```

## 使用場面

### シリアライザでの使用

```python
from apibase.serializers import BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'urn']

# レスポンス
{
    "id": 123,
    "name": "Product 1",
    "urn": "urn:products:product:123"
}
```

### リソースの参照

```python
# URNを使った関連リソースの参照
{
    "order_urn": "urn:orders:order:1",
    "items": [
        "urn:orders:orderitem:1",
        "urn:orders:orderitem:2"
    ]
}
```

### キャッシュキー

```python
from apibase.urn import model_urn

def get_cached_product(product_id):
    product = Product.objects.get(pk=product_id)
    cache_key = model_urn(product)  # "urn:products:product:123"
    return cache.get_or_set(cache_key, product)
```

## APIでの活用

### URNからエンドポイントへの変換

```python
from apibase.urn import rest_endpoint_from_urn

urn = "urn:products:product:123"
endpoint = rest_endpoint_from_urn(urn)
# "/api/rest/products/product/123/"
```

### URNからオブジェクトの取得

```python
def get_object_from_urn(urn_string):
    parts = urn_string.split(':')
    _, app_label, model_name, pk = parts

    from django.apps import apps
    model = apps.get_model(app_label, model_name)
    return model.objects.get(pk=pk)
```

## 他のシステムとの比較

### UUID

```
UUID: 550e8400-e29b-41d4-a716-446655440000
URN:  urn:products:product:123
```

- UUIDは完全にランダムで自己記述性がない
- URNはモデル情報を含み自己記述的

### URL

```
URL: https://api.example.com/products/123/
URN: urn:products:product:123
```

- URLは場所を示す（変更される可能性がある）
- URNはリソース自体を識別（永続的）

### GraphQL Global ID

```
GlobalID: UHJvZHVjdDoxMjM=  (Base64)
URN:      urn:products:product:123
```

- Global IDはBase64エンコードされている
- URNは人間が読める形式

## 実装の詳細

### model_urn関数

```python
def model_urn(instance, nss=None, nid=None):
    """モデルインスタンスからURNを生成"""
    nid = nid or instance._meta.app_label
    nss = nss or instance._meta.model_name
    return f"urn:{nid}:{nss}:{instance.pk}"
```

### UrnField

```python
class UrnField(fields.Field):
    def __init__(self, **kwargs):
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return model_urn(value)
```
