# バッチ作成

複数レコードを一括で作成する例です。

## 基本的なバッチ作成

### リクエスト

```bash
curl -X POST http://localhost:8000/api/products/batch_create/ \
  -H "Content-Type: application/json" \
  -d '[
    {"name": "商品A", "price": 1000, "stock": 10},
    {"name": "商品B", "price": 2000, "stock": 20},
    {"name": "商品C", "price": 3000, "stock": 30}
  ]'
```

### レスポンス

```json
[
    {
        "id": 1,
        "name": "商品A",
        "price": 1000,
        "stock": 10,
        "endpoint": "http://localhost:8000/api/products/1/",
        "urn": "urn:products:product:1",
        "display": "商品A"
    },
    {
        "id": 2,
        "name": "商品B",
        "price": 2000,
        "stock": 20,
        "endpoint": "http://localhost:8000/api/products/2/",
        "urn": "urn:products:product:2",
        "display": "商品B"
    },
    {
        "id": 3,
        "name": "商品C",
        "price": 3000,
        "stock": 30,
        "endpoint": "http://localhost:8000/api/products/3/",
        "urn": "urn:products:product:3",
        "display": "商品C"
    }
]
```

## バッチ更新

### リクエスト

```bash
curl -X PATCH http://localhost:8000/api/products/batch_update/ \
  -H "Content-Type: application/json" \
  -d '[
    {"id": 1, "price": 1100},
    {"id": 2, "price": 2100},
    {"id": 3, "stock": 25}
  ]'
```

## シリアライザの設定

バッチ更新に対応するには、シリアライザに設定が必要です:

```python
from apibase.serializers import (
    BaseModelSerializer,
    BatchSerializerMixin,
    BatchListSerializer
)

class ProductSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock']
        list_serializer_class = BatchListSerializer
        update_lookup_field = 'id'
```

## CSVからのバッチインポート

### Python例

```python
import csv
import requests

def import_products_from_csv(csv_file_path, api_url):
    products = []

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                'name': row['name'],
                'price': int(row['price']),
                'stock': int(row['stock'])
            })

    response = requests.post(
        f"{api_url}/batch_create/",
        json=products
    )

    return response.json()
```

### CSV例

```csv
name,price,stock
商品A,1000,10
商品B,2000,20
商品C,3000,30
```

## 関連データ付きのバッチ作成

注文と明細を同時に作成:

```bash
curl -X POST http://localhost:8000/api/orders/batch_create/ \
  -H "Content-Type: application/json" \
  -d '[
    {
      "order_number": "ORD-001",
      "customer": 1,
      "items": [
        {"product": 1, "quantity": 2},
        {"product": 2, "quantity": 1}
      ]
    },
    {
      "order_number": "ORD-002",
      "customer": 2,
      "items": [
        {"product": 3, "quantity": 3}
      ]
    }
  ]'
```

## トランザクション対応

すべての操作を1つのトランザクションで実行:

```python
from django.db import transaction

class ProductViewSet(BaseModelViewSet):
    @transaction.atomic
    def batch_create(self, request, *args, **kwargs):
        return super().batch_create(request, *args, **kwargs)
```
