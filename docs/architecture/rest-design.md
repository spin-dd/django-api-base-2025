# REST API設計思想

apibaseのREST API設計思想について説明します。

## 設計原則

### 1. リソース指向

すべてのエンドポイントはリソースを中心に設計されています。

```
/api/products/          # 商品リソース
/api/products/{id}/     # 特定の商品
/api/orders/            # 注文リソース
/api/orders/{id}/items/ # 注文に属する明細
```

### 2. HTTPメソッドの適切な使用

| メソッド | 用途 | 安全性 | べき等性 |
|---------|------|--------|---------|
| GET | 取得 | Yes | Yes |
| POST | 作成 | No | No |
| PUT | 完全更新 | No | Yes |
| PATCH | 部分更新 | No | Yes |
| DELETE | 削除 | No | Yes |

### 3. ステータスコードの適切な使用

| コード | 意味 | 使用場面 |
|--------|------|---------|
| 200 | OK | 正常なGET/PUT/PATCH |
| 201 | Created | 正常なPOST |
| 204 | No Content | 正常なDELETE |
| 400 | Bad Request | バリデーションエラー |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | 権限エラー |
| 404 | Not Found | リソースが存在しない |
| 500 | Server Error | サーバーエラー |

## レスポンス形式

### 単一リソース

```json
{
    "id": 1,
    "name": "Product 1",
    "price": 1000,
    "endpoint": "http://localhost:8000/api/products/1/",
    "urn": "urn:products:product:1",
    "display": "Product 1"
}
```

### リソース一覧

```json
{
    "count": 100,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [
        {"id": 1, "name": "Product 1", ...},
        {"id": 2, "name": "Product 2", ...}
    ]
}
```

### エラーレスポンス

```json
{
    "name": ["この項目は必須です。"],
    "price": ["この項目は正の整数である必要があります。"]
}
```

## バッチ操作

### バッチ作成

```
POST /api/products/batch_create/

[
    {"name": "Product 1", "price": 1000},
    {"name": "Product 2", "price": 2000}
]
```

### バッチ更新

```
PATCH /api/products/batch_update/

[
    {"id": 1, "price": 1500},
    {"id": 2, "price": 2500}
]
```

## フィルタリング

### クエリパラメータによるフィルタリング

```
GET /api/products/?category=electronics&price__gte=1000&price__lte=5000
```

### 検索

```
GET /api/products/?search=キーワード
```

### ソート

```
GET /api/products/?ordering=-price,name
```

### ページネーション

```
GET /api/products/?page=2&page_size=50
```

## メタデータ

### エンドポイントフィールド

各リソースには、自身のAPIエンドポイントURLが含まれます。

```json
{
    "endpoint": "http://localhost:8000/api/products/1/"
}
```

### URNフィールド

リソースを一意に識別するURNが含まれます。

```json
{
    "urn": "urn:products:product:1"
}
```

### 表示名フィールド

人間が読みやすい表示名が含まれます。

```json
{
    "display": "Product 1"
}
```

## HATEOAS

リソース間の関連はURLで表現されます。

```json
{
    "id": 1,
    "title": "Order 1",
    "customer": "http://localhost:8000/api/customers/1/",
    "items": [
        "http://localhost:8000/api/orders/1/items/1/",
        "http://localhost:8000/api/orders/1/items/2/"
    ]
}
```
