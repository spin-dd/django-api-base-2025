# モジュール構成

apibaseの各モジュールの役割と依存関係について説明します。

## モジュール一覧

```
apibase/
├── __init__.py
├── viewsets.py          # ViewSet拡張
├── serializers.py       # Serializer拡張
├── filters.py           # フィルタクラス
├── fields.py            # カスタムフィールド
├── routers.py           # URLルーター
├── paginations.py       # ページネーション
├── permissions.py       # 権限クラス
├── renderers.py         # レンダラー
├── utils.py             # ユーティリティ
├── urn.py               # URNシステム
├── storages.py          # ストレージ
├── archives.py          # アーカイブ
├── consumers.py         # WebSocketコンシューマ
├── graphql/             # GraphQL関連
│   ├── __init__.py
│   ├── mixins.py        # ミックスイン
│   ├── fields.py        # フィールド
│   ├── connections.py   # コネクション
│   ├── encoders.py      # エンコーダー
│   └── utils.py         # ユーティリティ
├── contrib/             # 追加機能
│   ├── schema/          # OpenAPIスキーマ
│   └── models/          # モデルユーティリティ
└── settings/            # 設定
    ├── __init__.py
    └── settings.py
```

## コアモジュール

### viewsets

**役割**: REST APIのViewSetを拡張

**主要クラス**:
- `BaseModelViewSet` - 拡張ModelViewSet
- `ViewSetMixin` - ユーティリティメソッド
- `DownloadMixin` - ファイルダウンロード

**依存関係**:
- `rest_framework.viewsets`
- `permissions`
- `paginations`
- `storages`
- `utils`

---

### serializers

**役割**: データシリアライゼーションを拡張

**主要クラス**:
- `BaseModelSerializer` - 拡張ModelSerializer
- `BatchSerializerMixin` - バッチ処理用
- `BatchListSerializer` - 一括更新用
- `EndpointField`, `UrnField`, `DisplayField` - カスタムフィールド

**依存関係**:
- `rest_framework.serializers`
- `urn`

---

### filters

**役割**: クエリフィルタリング

**主要クラス**:
- `BaseFilter` - 基底フィルタセット
- `WordFilter` - 日本語検索対応
- `ListCharInFilter`, `ListIntegerInFilter` - リストフィルタ
- `MonthFromToRangeFilter` - 月範囲フィルタ
- `CharRangeFilter` - 文字列範囲フィルタ

**依存関係**:
- `django_filters`
- `jaconv`
- `fields`

---

### graphql

**役割**: GraphQL API機能

**サブモジュール**:
- `mixins` - ObjectTypeミックスイン
- `fields` - カスタムフィールド
- `connections` - Relayコネクション
- `encoders` - JSONエンコーダー
- `utils` - ユーティリティ

**依存関係**:
- `graphene`
- `graphene_django`

## 依存関係図

```
                 ┌──────────────┐
                 │   settings   │
                 └──────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │   urn    │   │  utils   │   │  fields  │
  └──────────┘   └──────────┘   └──────────┘
         │              │              │
         ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │serializers│   │ storages │   │ filters  │
  └──────────┘   └──────────┘   └──────────┘
         │              │              │
         └──────────────┼──────────────┘
                        ▼
                 ┌──────────────┐
                 │   viewsets   │
                 └──────────────┘
```

## 拡張ポイント

### ViewSetの拡張

```python
from apibase.viewsets import BaseModelViewSet

class CustomViewSet(BaseModelViewSet):
    def get_queryset(self):
        # カスタムクエリセット
        return super().get_queryset().filter(active=True)
```

### Serializerの拡張

```python
from apibase.serializers import BaseModelSerializer

class CustomSerializer(BaseModelSerializer):
    def patch_result(self, instance, data):
        # 結果のカスタマイズ
        data['custom_field'] = 'value'
```

### Filterの拡張

```python
from apibase.filters import BaseFilter

class CustomFilter(BaseFilter):
    class Meta:
        model = MyModel
        fields = {'name': ['contains']}
```
