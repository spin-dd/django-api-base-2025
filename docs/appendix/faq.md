# よくある質問

apibaseに関するよくある質問と回答です。

## 一般

### apibaseとは何ですか？

apibaseは、Django REST FrameworkとGraphene-Djangoを拡張したライブラリです。ViewSet、Serializer、Filterなどの共通機能を提供し、API開発を効率化します。

### どのバージョンのDjangoに対応していますか？

Django 5.2以上に対応しています。Python 3.10〜3.12をサポートしています。

### ライセンスは何ですか？

MITライセンスです。商用利用も可能です。

## インストール

### pipでインストールできますか？

はい、pipでインストールできます:

```bash
pip install apibase
```

### オプション依存関係はどうやってインストールしますか？

```bash
# 開発用
pip install apibase[dev]

# ドキュメント用
pip install apibase[docs]

# OpenAPIスキーマ用
pip install apibase[schema]

# すべて
pip install apibase[all]
```

## ViewSet

### BaseModelViewSetと標準のModelViewSetの違いは？

BaseModelViewSetは以下の機能を追加しています:

- バッチ作成・更新（`batch_create`, `batch_update`）
- ファイルダウンロード（`DownloadMixin`）
- CSVエクスポート対応
- カスタムページネーション

### バッチ操作を無効にするには？

アクションをオーバーライドして無効にできます:

```python
class ProductViewSet(BaseModelViewSet):
    def batch_create(self, request, *args, **kwargs):
        return Response(status=405)  # Method Not Allowed
```

## Serializer

### endpoint/urn/displayフィールドを削除するには？

`Meta.fields`から除外するだけです:

```python
class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']  # endpoint等を含めない
```

### ネストシリアライザで削除もサポートしたい

削除フラグを使用したパターンを実装できます:

```python
class OrderItemSerializer(BaseModelSerializer):
    _delete = serializers.BooleanField(write_only=True, required=False)

class OrderSerializer(BaseModelSerializer):
    items = OrderItemSerializer(many=True)
    nested_fields = ['items']

    def update_nested_field(self, field_name, instance, validated_data, children):
        if field_name == 'items':
            for item_data in children or []:
                if item_data.get('_delete'):
                    OrderItem.objects.filter(id=item_data.get('id')).delete()
            children = [c for c in (children or []) if not c.get('_delete')]
        return super().update_nested_field(field_name, instance, validated_data, children)
```

## Filter

### WordFilterの検索がうまく動かない

以下を確認してください:

1. `lookups`に正しいフィールド名が指定されているか
2. フィールドがデータベースに存在するか
3. 関連フィールドの場合、`__`で正しく指定しているか

```python
search = WordFilter(
    lookups=['name', 'author__name'],  # 正しい
    lookups=['name', 'author.name'],   # 誤り
)
```

### 複数のフィルタセットを組み合わせたい

`clone_filter_fields`を使用:

```python
BookFilter.base_filters.update(
    clone_filter_fields(AuthorFilter, 'author')
)
```

## GraphQL

### REST APIとGraphQLを同時に使えますか？

はい、両方を同時に提供できます:

```python
urlpatterns = [
    path('api/', include('myapp.api.urls')),  # REST
    path('graphql/', GraphQLView.as_view()),   # GraphQL
]
```

### N+1問題を解決するには？

`select_related`/`prefetch_related`を使用:

```python
def resolve_books(self, info):
    return Book.objects.select_related('author').prefetch_related('tags')
```

## パフォーマンス

### 大量データの処理が遅い

以下を検討してください:

1. 適切なインデックスを追加
2. `select_related`/`prefetch_related`を使用
3. ページサイズを調整
4. キャッシュを導入

### CSVエクスポートでメモリが不足する

ストリーミングレスポンスを使用:

```python
from django.http import StreamingHttpResponse

def export_csv(self, request):
    def generate():
        for obj in self.get_queryset().iterator():
            yield f"{obj.id},{obj.name}\n"

    response = StreamingHttpResponse(generate(), content_type='text/csv')
    return response
```

## その他

### 質問や問題はどこに報告すればよいですか？

GitHubのIssueで報告してください:
https://github.com/spin-dd/django-api-base-2025/issues
