# Serializer活用ガイド

apibaseは、Django REST FrameworkのSerializerを拡張した機能を提供します。

## BaseModelSerializer

`BaseModelSerializer`は標準の`ModelSerializer`を拡張し、以下の機能を追加します:

- エンドポイントフィールド
- URNフィールド
- ディスプレイフィールド
- ネストシリアライザのサポート
- アクションハンドラー

### 基本的な使い方

```python
from apibase.serializers import BaseModelSerializer
from .models import Book

class BookSerializer(BaseModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'endpoint',  # 自動的にAPIエンドポイントURLを生成
            'urn',       # 自動的にURNを生成
            'display',   # モデルの__str__()を返す
        ]
```

## 特殊フィールド

### EndpointField

APIエンドポイントの絶対URLを自動生成します:

```python
from apibase.serializers import EndpointField

class BookSerializer(BaseModelSerializer):
    endpoint = EndpointField()  # デフォルト

    # カスタムURL名を指定
    custom_endpoint = EndpointField(url_name='api-book-detail')

    # 関連オブジェクトのエンドポイント
    author_endpoint = EndpointField(attr_name='author')
```

### UrnField

Uniform Resource Name (URN) を生成します:

```python
from apibase.serializers import UrnField

class BookSerializer(BaseModelSerializer):
    urn = UrnField()  # urn:app:model:pk 形式

    # 関連オブジェクトのURN
    author_urn = UrnField(attr_name='author')
```

### DisplayField

モデルの文字列表現を返します:

```python
from apibase.serializers import DisplayField

class BookSerializer(BaseModelSerializer):
    display = DisplayField()  # モデルの__str__()

    # 関連オブジェクトの表示名
    author_display = DisplayField(attr_name='author')
```

## ネストシリアライザ

`BaseModelSerializer`は、ネストされた関連オブジェクトの作成・更新をサポートします。

### 設定

```python
class ChapterSerializer(BaseModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'content']

class BookSerializer(BaseModelSerializer):
    chapters = ChapterSerializer(many=True, source='chapter_set')
    nested_fields = ['chapters']  # ネストフィールドとして登録

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'chapters']
```

### 使用例

```json
{
    "title": "Django入門",
    "author": "山田太郎",
    "chapters": [
        {"title": "第1章", "content": "はじめに"},
        {"title": "第2章", "content": "インストール"}
    ]
}
```

### シグナルによる通知

ネストフィールドの更新後にシグナルを送信できます:

```python
from django.dispatch import Signal

chapters_updated = Signal()

class BookSerializer(BaseModelSerializer):
    nested_fields = ['chapters']
    nested_fields_updateds_signal = chapters_updated
```

## アクションハンドラー

ViewSetのアクションに応じて異なる処理を実行できます:

```python
class CreateHandler:
    def __init__(self, serializer):
        self.serializer = serializer

    def validate(self):
        # create時のバリデーション
        pass

    def save(self, parent_save):
        # create時の保存処理
        instance = parent_save()
        return instance

class BookSerializer(BaseModelSerializer):
    action_handlers = {
        'create': CreateHandler,
        '*': DefaultHandler,  # その他すべてのアクション
    }
```

## update_or_create

シリアライザから直接レコードを更新または作成できます:

```python
# 新規作成
book = BookSerializer.update_or_create(
    title="新しい本",
    author="著者",
)

# 更新
book = BookSerializer.update_or_create(
    id=1,
    partial=True,
    title="更新されたタイトル",
)
```

## バッチ処理

### BatchSerializerMixin

バッチ更新用のミックスイン:

```python
from apibase.serializers import BatchSerializerMixin, BatchListSerializer

class BookSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author']
        list_serializer_class = BatchListSerializer
        update_lookup_field = 'id'
```

### BatchListSerializer

複数レコードの一括更新をサポート:

```python
# PATCH /api/books/batch_update/
[
    {"id": 1, "title": "更新タイトル1"},
    {"id": 2, "title": "更新タイトル2"}
]
```

## コンテキストの活用

シリアライザ内でリクエスト情報にアクセス:

```python
class BookSerializer(BaseModelSerializer):
    def create(self, validated_data):
        # 現在のアクション
        action = self.view_action  # 'create', 'update', etc.

        # リクエストユーザー
        user = self.request_user

        # ユーザーを設定して保存
        validated_data['created_by'] = user
        return super().create(validated_data)
```

## 結果のカスタマイズ

`patch_result`メソッドで出力をカスタマイズ:

```python
class BookSerializer(BaseModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author']

    def patch_result(self, instance, data):
        """シリアライズ結果をカスタマイズ"""
        data['summary'] = f"{instance.title} by {instance.author}"
```

## 次のステップ

- [ネストシリアライザチュートリアル](../tutorials/nested-serializers.md)
- [バッチ操作](batch-operations.md)
