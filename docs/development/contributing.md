# コントリビューションガイド

apibaseへの貢献方法について説明します。

## 貢献の方法

### Issue報告

バグや機能リクエストがある場合:

1. 既存のIssueを検索して重複がないか確認
2. 新しいIssueを作成
3. テンプレートに従って詳細を記載

### Pull Request

コードの変更を提案する場合:

1. リポジトリをフォーク
2. 機能ブランチを作成（`feature/your-feature`）
3. 変更をコミット
4. テストを追加・実行
5. Pull Requestを作成

## 開発フロー

### 1. フォークとクローン

```bash
# フォーク後
git clone https://github.com/your-username/django-api-base-2025.git
cd django-api-base-2025
git remote add upstream https://github.com/spin-dd/django-api-base-2025.git
```

### 2. ブランチ作成

```bash
git checkout -b feature/your-feature
```

### 3. 開発環境のセットアップ

```bash
uv sync --extra dev
```

### 4. 変更とテスト

```bash
# コードを変更
# ...

# テストを実行
uv run pytest

# リンターを実行
uv run ruff check apibase

# フォーマッターを実行
uv run black apibase
```

### 5. コミット

```bash
git add .
git commit -m "feat: add new feature"
```

### 6. プッシュとPR作成

```bash
git push origin feature/your-feature
# GitHubでPull Requestを作成
```

## コミットメッセージ

Conventional Commitsに従ってください:

```
<type>: <description>

[optional body]

[optional footer]
```

### タイプ

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードスタイルの変更
- `refactor`: リファクタリング
- `test`: テストの追加・修正
- `chore`: ビルドプロセス等の変更

### 例

```
feat: add WordFilter for Japanese search

Add WordFilter class that supports full-width/half-width conversion
for Japanese text search.

Closes #123
```

## コードレビュー

### レビュアーへの依頼

- PRの説明を明確に書く
- 変更の背景や意図を説明
- スクリーンショットや動作確認結果を添付

### レビュー時のポイント

- コードスタイルの一貫性
- テストの網羅性
- ドキュメントの更新
- 既存機能への影響

## ドキュメントの貢献

### ドキュメントの更新

```bash
# ドキュメントをビルド
uv sync --extra docs
uv run mkdocs serve

# ブラウザで http://localhost:8000 を確認
```

### 新しいページの追加

1. `docs/`にMarkdownファイルを作成
2. `mkdocs.yml`のnavセクションに追加

## 行動規範

- 他の貢献者を尊重する
- 建設的なフィードバックを心がける
- 異なる意見や視点を歓迎する
