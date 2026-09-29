# 開発者向け

apibaseの開発に参加するための情報です。

## コンテンツ

- [コントリビューションガイド](contributing.md) - 貢献の方法
- [開発環境構築](setup.md) - 環境のセットアップ
- [テスト方法](testing.md) - テストの実行
- [コーディング規約](coding-standards.md) - コードスタイル
- [リリースプロセス](release.md) - リリース手順
- [変更履歴](changelog.md) - バージョン履歴

## クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/spin-dd/django-api-base-2025.git
cd django-api-base-2025

# 依存関係をインストール
uv sync --extra dev

# テストを実行
uv run pytest

# ドキュメントをプレビュー
uv sync --extra docs
uv run mkdocs serve
```

## プロジェクト構成

```
django-api-base-2025/
├── apibase/          # メインパッケージ
├── docs/             # ドキュメント
├── scripts/          # スクリプト
├── tests/            # テスト
├── pyproject.toml    # プロジェクト設定
└── mkdocs.yml        # ドキュメント設定
```
