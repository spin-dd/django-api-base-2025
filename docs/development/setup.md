# 開発環境構築

開発環境のセットアップ方法を説明します。

## 前提条件

- Python 3.10以上
- uv（推奨）またはpip
- Git

## uvを使用する場合（推奨）

### 1. uvのインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. リポジトリのクローン

```bash
git clone https://github.com/spin-dd/django-api-base-2025.git
cd django-api-base-2025
```

### 3. 依存関係のインストール

```bash
# 開発用依存関係を含めてインストール
uv sync --extra dev

# ドキュメント用依存関係も含める場合
uv sync --extra dev --extra docs

# すべての依存関係
uv sync --extra all
```

### 4. 動作確認

```bash
# Pythonインタープリターを起動
uv run python

>>> import apibase
>>> apibase.__version__
```

## pipを使用する場合

### 1. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 開発モードでインストール

```bash
pip install -e ".[dev]"

# ドキュメント用
pip install -e ".[dev,docs]"
```

## IDEの設定

### VS Code

`.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

推奨拡張機能:

- Python
- Pylance
- Ruff
- Black Formatter

### PyCharm

1. File > Settings > Project > Python Interpreter
2. 仮想環境のインタープリターを選択
3. Tools > Python Integrated Tools
   - Docstring format: Google
   - Test runner: pytest

## テスト用Djangoプロジェクト

テストで使用するDjangoプロジェクトのセットアップ:

```python
# tests/conftest.py
import django
from django.conf import settings

def pytest_configure():
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'django_filters',
            'graphene_django',
        ],
        REST_FRAMEWORK={
            'DEFAULT_PAGINATION_CLASS': 'apibase.paginations.Pagination',
            'PAGE_SIZE': 20,
        },
    )
    django.setup()
```

## 依存関係の更新

```bash
# 依存関係を更新
uv lock --upgrade

# 特定のパッケージを更新
uv lock --upgrade-package django
```

## トラブルシューティング

### インポートエラー

```bash
# パッケージを再インストール
uv sync --reinstall
```

### キャッシュのクリア

```bash
uv cache clean
```
