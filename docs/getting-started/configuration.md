# 設定ガイド

apibaseの設定オプションについて説明します。

## apibase設定

`settings.py`に`APIBASE`辞書を追加して設定をカスタマイズできます:

```python
APIBASE = {
    'STORAGE_PREFIX': 'storage',
}
```

### 利用可能な設定

| 設定名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `STORAGE_PREFIX` | `'storage'` | ファイルダウンロードURLのプレフィックス |

## REST Framework設定

apibaseは Django REST Framework の設定を拡張します:

```python
REST_FRAMEWORK = {
    # ページネーション
    'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
    'PAGE_SIZE': 20,

    # フィルタバックエンド
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # レンダラー
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.CSVRenderer',  # CSV出力
    ],

    # 認証
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],

    # 権限
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

## GraphQL設定

GraphQL機能を使用する場合の設定:

```python
GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
}
```

### スキーマの作成例

```python
# myproject/schema.py
import graphene
from graphene_django import DjangoObjectType
from myapp.models import Book

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

class Query(graphene.ObjectType):
    books = graphene.List(BookType)
    book = graphene.Field(BookType, id=graphene.ID())

    def resolve_books(self, info):
        return Book.objects.all()

    def resolve_book(self, info, id):
        return Book.objects.get(pk=id)

schema = graphene.Schema(query=Query)
```

## Django Channels設定

WebSocket機能を使用する場合の設定:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'channels',
    'channels_redis',
]

ASGI_APPLICATION = 'myproject.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

```python
# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
            # WebSocketルーティング
        ])
    ),
})
```

## ログ設定

デバッグ用のログ設定:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apibase': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## OpenAPI スキーマ設定

drf-spectacularを使用する場合の設定:

```python
# オプション依存関係をインストール
# pip install apibase[schema]

REST_FRAMEWORK = {
    # ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'DESCRIPTION': 'APIドキュメント',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

## 次のステップ

設定が完了したら、各機能の詳細なガイドに進みましょう:

- [ViewSet活用ガイド](../guides/viewsets.md)
- [Serializer活用ガイド](../guides/serializers.md)
- [フィルタリング機能](../guides/filters.md)
