# 基本的なAPI構築

このチュートリアルでは、apibaseを使って書籍管理APIを構築します。

## ゴール

- モデルの作成
- シリアライザの実装
- フィルタの設定
- ViewSetの作成
- URLルーティングの設定

## 1. プロジェクトのセットアップ

### Djangoプロジェクトの作成

```bash
# プロジェクト作成
django-admin startproject bookstore
cd bookstore

# アプリケーション作成
python manage.py startapp books
```

### settings.py の設定

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # サードパーティ
    'rest_framework',
    'django_filters',

    # アプリケーション
    'books',
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

## 2. モデルの作成

### books/models.py

```python
from django.db import models


class Author(models.Model):
    name = models.CharField('名前', max_length=100)
    email = models.EmailField('メールアドレス', blank=True)
    bio = models.TextField('経歴', blank=True)

    class Meta:
        verbose_name = '著者'
        verbose_name_plural = '著者'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField('カテゴリ名', max_length=50)
    slug = models.SlugField('スラッグ', unique=True)

    class Meta:
        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField('タイトル', max_length=200)
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name='books',
        verbose_name='著者'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='カテゴリ'
    )
    isbn = models.CharField('ISBN', max_length=13, unique=True)
    price = models.PositiveIntegerField('価格')
    published_date = models.DateField('出版日')
    description = models.TextField('説明', blank=True)
    is_available = models.BooleanField('在庫あり', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        verbose_name = '書籍'
        verbose_name_plural = '書籍'
        ordering = ['-published_date']

    def __str__(self):
        return self.title
```

### マイグレーション

```bash
python manage.py makemigrations books
python manage.py migrate
```

## 3. シリアライザの作成

### books/api/serializers.py

```python
from apibase.serializers import BaseModelSerializer
from ..models import Author, Category, Book


class AuthorSerializer(BaseModelSerializer):
    class Meta:
        model = Author
        fields = [
            'id',
            'name',
            'email',
            'bio',
            'endpoint',
            'urn',
            'display',
        ]


class CategorySerializer(BaseModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'endpoint',
            'urn',
            'display',
        ]


class BookSerializer(BaseModelSerializer):
    # 関連オブジェクトの読み取り用
    author_display = serializers.CharField(source='author.name', read_only=True)
    category_display = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'author_display',
            'category',
            'category_display',
            'isbn',
            'price',
            'published_date',
            'description',
            'is_available',
            'created_at',
            'updated_at',
            'endpoint',
            'urn',
            'display',
        ]
        read_only_fields = ['created_at', 'updated_at']
```

## 4. フィルタの作成

### books/api/filters.py

```python
from apibase.filters import BaseFilter, WordFilter
import django_filters
from ..models import Author, Category, Book


class AuthorFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['name', 'email'],
    )

    class Meta:
        model = Author
        fields = {
            'name': ['exact', 'contains'],
        }


class CategoryFilter(BaseFilter):
    class Meta:
        model = Category
        fields = {
            'name': ['exact', 'contains'],
            'slug': ['exact'],
        }


class BookFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['title', 'author__name', 'description'],
    )

    # 価格の範囲フィルタ
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='最低価格'
    )
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='最高価格'
    )

    # 出版日の範囲フィルタ
    published_after = django_filters.DateFilter(
        field_name='published_date',
        lookup_expr='gte',
        label='出版日（以降）'
    )
    published_before = django_filters.DateFilter(
        field_name='published_date',
        lookup_expr='lte',
        label='出版日（以前）'
    )

    class Meta:
        model = Book
        fields = {
            'title': ['exact', 'contains'],
            'author': ['exact'],
            'category': ['exact'],
            'isbn': ['exact'],
            'is_available': ['exact'],
        }
```

## 5. ViewSetの作成

### books/api/viewsets.py

```python
from apibase.viewsets import BaseModelViewSet
from ..models import Author, Category, Book
from .serializers import AuthorSerializer, CategorySerializer, BookSerializer
from .filters import AuthorFilter, CategoryFilter, BookFilter


class AuthorViewSet(BaseModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filterset_class = AuthorFilter
    ordering_fields = ['name', 'id']
    search_fields = ['name', 'email']


class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_class = CategoryFilter
    ordering_fields = ['name', 'slug']


class BookViewSet(BaseModelViewSet):
    queryset = Book.objects.select_related('author', 'category').all()
    serializer_class = BookSerializer
    filterset_class = BookFilter
    ordering_fields = ['title', 'price', 'published_date', 'created_at']
    search_fields = ['title', 'author__name', 'isbn']
```

## 6. URLルーティング

### books/api/urls.py

```python
from rest_framework.routers import DefaultRouter
from .viewsets import AuthorViewSet, CategoryViewSet, BookViewSet

router = DefaultRouter()
router.register('authors', AuthorViewSet)
router.register('categories', CategoryViewSet)
router.register('books', BookViewSet)

urlpatterns = router.urls
```

### bookstore/urls.py

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('books.api.urls')),
]
```

## 7. 動作確認

### サーバー起動

```bash
python manage.py runserver
```

### APIのテスト

```bash
# 著者一覧
curl http://localhost:8000/api/authors/

# 著者作成
curl -X POST http://localhost:8000/api/authors/ \
  -H "Content-Type: application/json" \
  -d '{"name": "山田太郎", "email": "yamada@example.com"}'

# カテゴリ作成
curl -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "プログラミング", "slug": "programming"}'

# 書籍作成
curl -X POST http://localhost:8000/api/books/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Django入門",
    "author": 1,
    "category": 1,
    "isbn": "9784123456789",
    "price": 3000,
    "published_date": "2024-01-15"
  }'

# 検索
curl "http://localhost:8000/api/books/?search=Django"

# フィルタリング
curl "http://localhost:8000/api/books/?price_min=2000&price_max=4000"

# バッチ作成
curl -X POST http://localhost:8000/api/books/batch_create/ \
  -H "Content-Type: application/json" \
  -d '[
    {"title": "Book 1", "author": 1, "isbn": "1234567890123", "price": 1000, "published_date": "2024-01-01"},
    {"title": "Book 2", "author": 1, "isbn": "1234567890124", "price": 2000, "published_date": "2024-02-01"}
  ]'
```

## 次のステップ

- [GraphQL API構築](graphql-api.md)
- [ネストシリアライザ](nested-serializers.md)
- [テストの書き方](testing.md)
