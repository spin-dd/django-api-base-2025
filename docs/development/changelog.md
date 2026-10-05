# 変更履歴

apibaseの変更履歴です。

## v0.4.8 (2026-10-05)

### Fixed

- 入れ子保存と一括保存で、後続の検証・制約エラー時に先行更新を巻き戻す。
- 一括保存で各親に対応する子データを保持し、省略と空配列を親ごとに区別する。
- 一括更新で識別子を省略した入力を400で断る。
- 一括更新の対象instanceが選ぶDBで全件を保護し、複数DBへの更新は保存前に断る。

## v0.2.1

### Fixed

- drf-spectacularをオプション依存として扱うよう修正
- DownloadMixinにdrf-spectacular用の@extend_schemaを追加
- utilsモジュールのインポートを直接インポートに変更

## v0.2.0

### Added

- BaseModelViewSetにバッチ操作機能を追加
  - `batch_create`: 一括作成
  - `batch_update`: 一括更新
- WordFilterで日本語検索をサポート
  - 全角/半角自動変換
  - 複数キーワードAND検索
- GraphQL統合機能
  - CountableConnection
  - カスタムフィールド
- ドキュメントをMkDocsで作成

### Changed

- Pagination設定をカスタマイズ可能に
- シリアライザのネストフィールド処理を改善

### Fixed

- CSVエクスポート時のエンコーディング問題を修正
- フィルタのdistinct処理を修正

## v0.1.0

### Added

- 初期リリース
- BaseModelViewSet
- BaseModelSerializer
- BaseFilter
- URNシステム
- DownloadMixin

---

## バージョニングポリシー

このプロジェクトは[セマンティックバージョニング](https://semver.org/lang/ja/)に従います。

- **MAJOR**: 後方互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

## 貢献

変更履歴はPull Requestのマージ時に更新されます。
各変更は適切なカテゴリに分類してください:

- **Added**: 新機能
- **Changed**: 既存機能の変更
- **Deprecated**: 非推奨になった機能
- **Removed**: 削除された機能
- **Fixed**: バグ修正
- **Security**: セキュリティ関連の修正
