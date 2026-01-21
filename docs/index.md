# apibase

Django REST Framework と GraphQL (Graphene) を拡張したライブラリです。

## 特徴

apibaseは、Django REST FrameworkおよびGrapheneを拡張し、以下の機能を提供します:

- **ViewSet拡張**: バッチ作成・更新、ファイルダウンロード機能を備えた拡張ViewSet
- **Serializer拡張**: ネストシリアライザ対応、URNフィールド、エンドポイントフィールド
- **フィルタリング**: 日本語対応のWordFilter、範囲フィルタ、リストフィルタ
- **GraphQL統合**: Graphene-Djangoとの統合、カスタムフィールド、コネクション
- **WebSocket**: Django Channelsとの統合
- **ユーティリティ**: URNシステム、ストレージ、アーカイブ機能

## クイックスタート

### インストール

```bash
pip install apibase
```

または `uv` を使用:

```bash
uv add apibase
```

### 基本的な使い方

```python
from apibase.viewsets import BaseModelViewSet
from apibase.serializers import BaseModelSerializer
from apibase.filters import BaseFilter

class BookSerializer(BaseModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'endpoint', 'urn', 'display']

class BookFilter(BaseFilter):
    class Meta:
        model = Book
        fields = {
            'title': ['exact', 'contains'],
            'author': ['exact'],
        }

class BookViewSet(BaseModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filterset_class = BookFilter
```

## ドキュメント構成

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } **はじめに**

    ---

    インストール方法、クイックスタート、基本設定

    [:octicons-arrow-right-24: はじめに](getting-started/index.md)

-   :material-book-open-variant:{ .lg .middle } **ガイド**

    ---

    各機能の詳細な使い方ガイド

    [:octicons-arrow-right-24: ガイド](guides/index.md)

-   :material-school:{ .lg .middle } **チュートリアル**

    ---

    ステップバイステップのチュートリアル

    [:octicons-arrow-right-24: チュートリアル](tutorials/index.md)

-   :material-cog:{ .lg .middle } **アーキテクチャ**

    ---

    設計思想とモジュール構成

    [:octicons-arrow-right-24: アーキテクチャ](architecture/index.md)

-   :material-api:{ .lg .middle } **APIリファレンス**

    ---

    クラス・関数の詳細リファレンス

    [:octicons-arrow-right-24: APIリファレンス](reference/index.md)

-   :material-code-tags:{ .lg .middle } **実例集**

    ---

    実践的なコード例

    [:octicons-arrow-right-24: 実例集](examples/index.md)

</div>

## 対応バージョン

| パッケージ | バージョン |
|-----------|-----------|
| Python | 3.10 - 3.12 |
| Django | 5.2.x |
| Django REST Framework | 3.16+ |
| Graphene-Django | 3.2+ |
| Django Channels | 4.3+ |

## ライセンス

MIT License
