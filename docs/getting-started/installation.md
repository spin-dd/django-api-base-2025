# インストール

## パッケージのインストール

### pip を使用

```bash
pip install apibase
```

### uv を使用

```bash
uv add apibase
```

### Poetry を使用

```bash
poetry add apibase
```

## オプション依存関係

apibaseには、いくつかのオプション依存関係があります:

### 開発ツール

```bash
pip install apibase[dev]
```

含まれるパッケージ:

- pytest - テストフレームワーク
- black - コードフォーマッター
- ruff - リンター

### OpenAPI スキーマ

```bash
pip install apibase[schema]
```

含まれるパッケージ:

- drf-spectacular - OpenAPIスキーマ生成

### ドキュメント

```bash
pip install apibase[docs]
```

含まれるパッケージ:

- mkdocs - ドキュメント生成
- mkdocs-material - Material テーマ
- mkdocstrings - APIドキュメント自動生成

### すべてのオプション

```bash
pip install apibase[all]
```

## Django設定

`settings.py` に以下を追加します:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'django_filters',
    'channels',
    'graphene_django',

    # Your apps
    'myapp',
]

# REST Framework 設定
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# GraphQL 設定
GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',
}
```

## 動作確認

インストールが正しく完了したかを確認します:

```python
>>> import apibase
>>> apibase.__version__
'0.2.1'
```

## 次のステップ

インストールが完了したら、[クイックスタート](quick-start.md)に進みましょう。
