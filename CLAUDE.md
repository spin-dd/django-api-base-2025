# CLAUDE.md - apibase プロジェクト知識ベース

## プロジェクト概要

**apibase**はDjango REST FrameworkとGraphene-Djangoを拡張したライブラリ。API開発を効率化するViewSet、Serializer、Filterなどの共通機能を提供。

- **対応バージョン**: Django 5.2以上、Python 3.10〜3.12
- **ライセンス**: MIT
- **メインブランチ**: master
- **開発ブランチ**: v2025

## ドキュメント

### ドキュメント構造 (`docs/`)

```
docs/
├── index.md                    # トップページ
├── getting-started/            # インストール、クイックスタート、設定
├── guides/                     # ViewSet、Serializer、Filter、GraphQL等の活用ガイド
├── tutorials/                  # 実践的なチュートリアル
├── architecture/               # 設計思想、モジュール構成
├── reference/                  # APIリファレンス
│   ├── graphql/               # GraphQL関連API
│   └── contrib/               # contrib関連API
├── examples/                   # コード例集
├── development/                # 開発者向けガイド
└── appendix/                   # FAQ、トラブルシューティング、用語集
```

### ドキュメントビルド

```bash
# 依存関係インストール
uv sync --extra docs

# ローカルサーバー起動 (http://localhost:8000)
uv run mkdocs serve

# 静的サイトビルド (site/に出力)
uv run mkdocs build --strict
```

## 主要モジュール

### apibase.viewsets
- `BaseModelViewSet`: ModelViewSetの拡張。バッチ操作、ファイルダウンロード対応
- `DownloadMixin`: ファイルダウンロード機能を追加

### apibase.serializers
- `BaseModelSerializer`: ModelSerializerの拡張
  - 自動フィールド: `endpoint`, `urn`, `display`
  - `nested_fields`: ネストシリアライザの自動処理

### apibase.filters
- `BaseFilter`: FilterSetの拡張
- `WordFilter`: 日本語検索対応フィルタ（全角/半角変換、複数キーワードAND検索）
- `clone_filter_fields()`: フィルタフィールドの複製

### apibase.urn
- URN形式: `urn:{app}:{model}:{pk}`
- `to_urn()`: オブジェクトからURN生成
- `from_urn()`: URNからオブジェクト取得

### apibase.graphql
- `mixins.py`: GraphQL用Mixin
- `fields.py`: カスタムGraphQLフィールド
- `connections.py`: Relay仕様のConnection実装

### apibase.contrib
- `schema.py`: drf-spectacular連携（optional dependency）
- `models.py`: 共通モデル機能

## 設定 (`pyproject.toml`)

### 依存関係グループ

```toml
[project.optional-dependencies]
dev = ["pytest", "pytest-django", "pytest-cov", ...]
docs = ["mkdocs", "mkdocs-material", "mkdocstrings[python]", ...]
schema = ["drf-spectacular"]
all = ["apibase[dev,docs,schema]"]
```

## GitHub Actions

### `.github/workflows/docs.yml`
- push/PRでドキュメントビルド
- masterへのpushでGitHub Pagesデプロイ
- タグ付きリリースでmikeによるバージョン管理

### `.github/workflows/release-docs.yml` (未コミット)
- 手動トリガーでリリース作成
- v2025ブランチからdocs.zipを生成

## コーディングパターン

### ViewSetパターン
```python
from apibase.viewsets import BaseModelViewSet

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
```

### Serializerパターン
```python
from apibase.serializers import BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'endpoint', 'urn', 'display']
```

### Filterパターン
```python
from apibase.filters import BaseFilter, WordFilter

class ProductFilter(BaseFilter):
    search = WordFilter(lookups=['name', 'description'])

    class Meta:
        model = Product
        fields = {'category': ['exact'], 'price': ['gte', 'lte']}
```

### ネストシリアライザパターン
```python
class OrderSerializer(BaseModelSerializer):
    items = OrderItemSerializer(many=True)
    nested_fields = ['items']  # 自動的に作成・更新処理

    class Meta:
        model = Order
        fields = ['id', 'customer', 'items']
```

## 参照プロジェクト

- **taihei-cvm-server**: apibaseを使用した実践的なプロジェクト例
  - `web/base/api/filters.py`: フィルタ実装例
  - `web/base/api/serializers.py`: シリアライザ実装例
  - `web/contracts/api/viewsets.py`: ViewSet実装例
  - `web/contracts/api/gql/`: GraphQL実装例

## 注意事項

- drf-spectacularはoptional dependency（インストールされていない場合はスキップ）
- `DownloadMixin`使用時は`@extend_schema`デコレータが必要（drf-spectacular対応）
- GraphQL使用時は`graphene-django`が必要
- WebSocket使用時は`channels`と`channels-redis`が必要
