# serializers

Serializer拡張クラスを提供するモジュールです。

## クラス

### BaseModelSerializer

`rest_framework.serializers.ModelSerializer`を拡張した基底クラスです。

```python
from apibase.serializers import BaseModelSerializer
```

**属性**

| 属性 | 型 | 説明 |
|-----|-----|------|
| `id` | `IntegerField` | 主キー（読み取り/書き込み可） |
| `endpoint` | `EndpointField` | APIエンドポイントURL |
| `urn` | `UrnField` | Uniform Resource Name |
| `display` | `DisplayField` | 文字列表現 |
| `nested_fields` | `list[str]` | ネストフィールド名のリスト |
| `nested_fields_updateds_signal` | `Signal` | ネスト更新後に送信するシグナル |
| `action_handlers` | `dict` | アクションハンドラーのマッピング |

**プロパティ**

#### view_action

```python
@property
def view_action(self) -> str | None
```

現在のViewSetアクション名を取得します。

#### request_user

```python
@property
def request_user(self) -> User | None
```

リクエストユーザーを取得します。

#### children_set

```python
@property
def children_set(self) -> dict
```

ネストフィールドのデータセットを取得します。

**メソッド**

#### update_or_create

```python
@classmethod
def update_or_create(cls, partial=None, id=None, context=None, **validated_data)
```

レコードを更新または作成します。

**引数**

- `partial` - 部分更新かどうか
- `id` - 更新対象のID（Noneの場合は新規作成）
- `context` - シリアライザコンテキスト
- `**validated_data` - フィールドデータ

**戻り値**

- モデルインスタンス

#### patch_result

```python
def patch_result(self, instance, data)
```

シリアライズ結果をカスタマイズするためのフックメソッド。

**引数**

- `instance` - モデルインスタンス
- `data` - シリアライズされたデータ（変更可能）

#### update_nested

```python
def update_nested(self, instance, validated_data, field_name, children)
```

ネストされた関連オブジェクトを更新します。

#### patch_children

```python
def patch_children(self, instance, field_name, data) -> dict
```

ネスト子要素のデータを変更するためのフック。

---

### UrnModelSerializer

URNフィールドのみを持つ軽量シリアライザです。

```python
from apibase.serializers import UrnModelSerializer
```

---

### BatchSerializerMixin

バッチ更新用のミックスインです。

```python
from apibase.serializers import BatchSerializerMixin
```

**使用方法**

```python
class ProductSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
        list_serializer_class = BatchListSerializer
        update_lookup_field = 'id'
```

---

### BatchListSerializer

バッチ更新用のListSerializerです。

```python
from apibase.serializers import BatchListSerializer
```

**属性**

- `update_lookup_field` - 更新時のルックアップフィールド（デフォルト: `'id'`）

**メソッド**

#### update

```python
def update(self, queryset, all_validated_data)
```

複数オブジェクトを一括更新します。

---

## フィールド

### EndpointField

APIエンドポイントURLを生成するフィールドです。

```python
from apibase.serializers import EndpointField
```

**引数**

- `url_name` - URL名（オプション）
- `attr_name` - 関連オブジェクトの属性名（オプション）

**使用例**

```python
class BookSerializer(BaseModelSerializer):
    endpoint = EndpointField()
    author_endpoint = EndpointField(attr_name='author')
```

---

### UrnField

Uniform Resource Nameを生成するフィールドです。

```python
from apibase.serializers import UrnField
```

**引数**

- `attr_name` - 関連オブジェクトの属性名（オプション）

**生成形式**

```
urn:{app_label}:{model_name}:{pk}
```

---

### DisplayField

モデルの文字列表現を返すフィールドです。

```python
from apibase.serializers import DisplayField
```

**引数**

- `attr_name` - 関連オブジェクトの属性名（オプション）

---

## 関数

### to_urn

```python
def to_urn(instance, nss=None, nid=None) -> str
```

モデルインスタンスからURNを生成します。

### endpoint_from_urn

```python
def endpoint_from_urn(urn, domain=None, nid=None, prefix="/api/rest", request=None) -> str
```

URNからエンドポイントURLを生成します。

### drf_endpoint

```python
def drf_endpoint(instance, url_name=None, pk_name="pk") -> str
```

DRFエンドポイントURLを生成します。

---

## 使用例

### 基本的な使用

```python
from apibase.serializers import BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'endpoint', 'urn', 'display']
```

### ネストシリアライザ

```python
class OrderItemSerializer(BaseModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']

class OrderSerializer(BaseModelSerializer):
    items = OrderItemSerializer(many=True)
    nested_fields = ['items']

    class Meta:
        model = Order
        fields = ['id', 'customer', 'items']
```

### アクションハンドラー

```python
class CreateHandler:
    def __init__(self, serializer):
        self.serializer = serializer

    def validate(self):
        pass

    def save(self, parent_save):
        return parent_save()

class ProductSerializer(BaseModelSerializer):
    action_handlers = {
        'create': CreateHandler,
    }
```
