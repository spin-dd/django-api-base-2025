# settings

apibaseの設定モジュールです。

## 設定クラス

### ApibaseSettings

apibaseの設定を管理するクラスです。

```python
from apibase.settings import apibase_settings
```

---

## 設定項目

### STORAGE_PREFIX

ファイルダウンロードURLのプレフィックスです。

| 項目 | 値 |
|-----|-----|
| デフォルト | `'storage'` |
| 型 | `str` |

---

## 設定方法

### settings.py での設定

```python
APIBASE = {
    'STORAGE_PREFIX': 'files',
}
```

---

## 使用例

### 設定値の参照

```python
from apibase.settings import apibase_settings

prefix = apibase_settings.STORAGE_PREFIX
# 'storage' (デフォルト) または設定された値
```

### ViewSetでの使用

```python
from rest_framework import decorators
from apibase.settings import apibase_settings

class DocumentViewSet(BaseModelViewSet):
    @decorators.action(
        methods=['get'],
        detail=False,
        url_path=rf'{apibase_settings.STORAGE_PREFIX}/(?P<field>[^/]+)/(?P<name>.+)'
    )
    def download_storage(self, request, field=None, name=None):
        # ...
```

---

## Django REST Framework設定

apibaseと組み合わせて使用する推奨設定:

```python
REST_FRAMEWORK = {
    # ページネーション
    'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
    'PAGE_SIZE': 20,

    # フィルタ
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # レンダラー
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    ],
}
```

---

## GraphQL設定

```python
GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
    'MIDDLEWARE': [],
}
```

---

## Channels設定

```python
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
