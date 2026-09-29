# リリースプロセス

apibaseのリリース手順について説明します。

## バージョニング

セマンティックバージョニング（SemVer）を採用:

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: 後方互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

## リリース手順

### 1. リリースブランチの作成

```bash
git checkout -b release/v0.3.0
```

### 2. バージョン更新

`pyproject.toml`のバージョンを更新:

```toml
[project]
version = "0.3.0"
```

### 3. 変更履歴の更新

`docs/development/changelog.md`を更新:

```markdown
## v0.3.0 (2024-01-15)

### Added
- 新機能の説明

### Changed
- 変更点の説明

### Fixed
- 修正内容の説明
```

### 4. テストの実行

```bash
uv run pytest
uv run ruff check apibase
```

### 5. コミットとタグ

```bash
git add .
git commit -m "chore: release v0.3.0"
git tag v0.3.0
git push origin release/v0.3.0
git push origin v0.3.0
```

### 6. Pull Requestの作成

- `release/v0.3.0` → `master` へのPRを作成
- レビューを依頼

### 7. マージとリリース

PRがマージされたら:

```bash
git checkout master
git pull origin master
```

### 8. PyPIへの公開（任意）

```bash
uv build
uv publish
```

## ドキュメントのデプロイ

### mikeを使用したバージョン管理

```bash
# ドキュメントをビルドしてデプロイ
uv run mike deploy --push --update-aliases 0.3.0 latest

# デフォルトバージョンを設定
uv run mike set-default --push latest
```

## ホットフィックス

緊急のバグ修正が必要な場合:

### 1. ホットフィックスブランチの作成

```bash
git checkout -b hotfix/v0.2.2 v0.2.1
```

### 2. 修正を適用

```bash
# 修正をコミット
git commit -m "fix: 緊急修正の説明"
```

### 3. バージョン更新

```toml
version = "0.2.2"
```

### 4. タグとマージ

```bash
git tag v0.2.2
git checkout master
git merge hotfix/v0.2.2
git push origin master
git push origin v0.2.2
```

## チェックリスト

リリース前の確認事項:

- [ ] すべてのテストがパス
- [ ] リンターエラーなし
- [ ] ドキュメントが更新済み
- [ ] 変更履歴が更新済み
- [ ] バージョン番号が更新済み
- [ ] マイグレーションが必要な場合は記載済み
