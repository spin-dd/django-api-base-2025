# urn

URN（Uniform Resource Name）システムを提供するモジュールです。

## 概要

URNは、リソースを一意に識別するための永続的な識別子です。apibaseのURNシステムは、Djangoモデルインスタンスを識別するために使用されます。

## URNの形式

```
urn:{nid}:{nss}:{identifier}
```

- `nid` - Namespace Identifier（デフォルト: アプリケーション名）
- `nss` - Namespace Specific String（デフォルト: モデル名）
- `identifier` - リソース識別子（デフォルト: 主キー）

例: `urn:myapp:product:123`

---

## 関数

### model_urn

```python
def model_urn(instance, nss=None, nid=None) -> str
```

モデルインスタンスからURNを生成します。

**引数**

- `instance` - モデルインスタンス
- `nss` - Namespace Specific String（オプション）
- `nid` - Namespace Identifier（オプション）

**戻り値**

- `str` - URN文字列

**使用例**

```python
from apibase.urn import model_urn

product = Product.objects.get(pk=1)
urn = model_urn(product)
# "urn:products:product:1"
```

---

### rest_endpoint_from_urn

```python
def rest_endpoint_from_urn(urn, domain=None, nid=None, prefix="/api/rest", request=None) -> str
```

URNからREST APIエンドポイントURLを生成します。

**引数**

- `urn` - URN文字列
- `domain` - ドメイン（オプション）
- `nid` - Namespace Identifier（オプション）
- `prefix` - URLプレフィックス
- `request` - リクエストオブジェクト（絶対URL生成用）

**戻り値**

- `str` - エンドポイントURL

**使用例**

```python
from apibase.urn import rest_endpoint_from_urn

url = rest_endpoint_from_urn("urn:products:product:1")
# "/api/rest/products/product/1/"
```

---

## シリアライザでの使用

### UrnField

```python
from apibase.serializers import UrnField, BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    urn = UrnField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'urn']
```

レスポンス例:

```json
{
    "id": 1,
    "name": "Product 1",
    "urn": "urn:products:product:1"
}
```

---

## 使用例

### URNからオブジェクトを取得

```python
from apibase.urn import parse_urn

def get_object_from_urn(urn_string):
    """URNからオブジェクトを取得"""
    parts = urn_string.split(':')
    if len(parts) != 4 or parts[0] != 'urn':
        raise ValueError("Invalid URN format")

    _, app_label, model_name, pk = parts

    from django.apps import apps
    model = apps.get_model(app_label, model_name)
    return model.objects.get(pk=pk)
```

### 複数オブジェクトのURN生成

```python
from apibase.urn import model_urn

products = Product.objects.all()
urns = [model_urn(p) for p in products]
```
