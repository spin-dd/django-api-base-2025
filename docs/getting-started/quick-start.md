# クイックスタート

このガイドでは、apibaseを使って基本的なREST APIを構築する方法を説明します。

## 1. モデルの作成

まず、Djangoモデルを作成します:

```python
# myapp/models.py
from django.db import models

class Book(models.Model):
    title = models.CharField('タイトル', max_length=200)
    author = models.CharField('著者', max_length=100)
    published_date = models.DateField('出版日')
    isbn = models.CharField('ISBN', max_length=13, unique=True)

    class Meta:
        verbose_name = '書籍'
        verbose_name_plural = '書籍'

    def __str__(self):
        return self.title
```

## 2. Serializerの作成

`BaseModelSerializer`を使用してシリアライザを作成します:

```python
# myapp/api/serializers.py
from apibase.serializers import BaseModelSerializer
from ..models import Book

class BookSerializer(BaseModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'published_date',
            'isbn',
            'endpoint',  # APIエンドポイントURL
            'urn',       # Uniform Resource Name
            'display',   # 文字列表現
        ]
```

## 3. Filterの作成

`BaseFilter`を使用してフィルタを作成します:

```python
# myapp/api/filters.py
from apibase.filters import BaseFilter, WordFilter
from ..models import Book

class BookFilter(BaseFilter):
    # 日本語検索対応フィルタ
    search = WordFilter(
        label='検索',
        lookups=['title', 'author'],
    )

    class Meta:
        model = Book
        fields = {
            'title': ['exact', 'contains'],
            'author': ['exact', 'contains'],
            'published_date': ['exact', 'gte', 'lte'],
        }
```

## 4. ViewSetの作成

`BaseModelViewSet`を使用してViewSetを作成します:

```python
# myapp/api/viewsets.py
from apibase.viewsets import BaseModelViewSet
from ..models import Book
from .serializers import BookSerializer
from .filters import BookFilter

class BookViewSet(BaseModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filterset_class = BookFilter
```

## 5. URLルーティング

ルーターを使用してURLを設定します:

```python
# myapp/api/urls.py
from rest_framework.routers import DefaultRouter
from .viewsets import BookViewSet

router = DefaultRouter()
router.register('books', BookViewSet)

urlpatterns = router.urls
```

```python
# myproject/urls.py
from django.urls import path, include

urlpatterns = [
    path('api/', include('myapp.api.urls')),
]
```

## 6. APIの使用

APIが利用可能になりました:

### 一覧取得

```bash
curl http://localhost:8000/api/books/
```

レスポンス:

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Djangoガイド",
            "author": "山田太郎",
            "published_date": "2024-01-15",
            "isbn": "9784123456789",
            "endpoint": "http://localhost:8000/api/books/1/",
            "urn": "urn:myapp:book:1",
            "display": "Djangoガイド"
        }
    ]
}
```

### 検索

```bash
# タイトルで検索
curl "http://localhost:8000/api/books/?search=Django"

# フィルタリング
curl "http://localhost:8000/api/books/?author__contains=山田"
```

### バッチ作成

```bash
curl -X POST http://localhost:8000/api/books/batch_create/ \
  -H "Content-Type: application/json" \
  -d '[
    {"title": "Book 1", "author": "Author 1", "published_date": "2024-01-01", "isbn": "1234567890123"},
    {"title": "Book 2", "author": "Author 2", "published_date": "2024-02-01", "isbn": "1234567890124"}
  ]'
```

## 次のステップ

- [設定ガイド](configuration.md) - 詳細な設定オプション
- [ViewSet活用ガイド](../guides/viewsets.md) - ViewSetの詳細な使い方
- [フィルタリング機能](../guides/filters.md) - 高度なフィルタリング
