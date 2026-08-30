# アーキテクチャ

apibaseの設計思想とアーキテクチャについて説明します。

## コンテンツ

- [全体像](overview.md) - システム全体の構成
- [モジュール構成](modules.md) - 各モジュールの役割
- [REST API設計思想](rest-design.md) - REST APIの設計方針
- [GraphQL設計思想](graphql-design.md) - GraphQL APIの設計方針
- [URNシステム](urn-system.md) - リソース識別システム
- [設計判断](design-decisions.md) - 技術的な設計判断

## 設計原則

apibaseは以下の原則に基づいて設計されています:

1. **DRY（Don't Repeat Yourself）** - 共通処理を抽象化
2. **規約より設定** - 合理的なデフォルト値の提供
3. **拡張性** - 継承やミックスインによるカスタマイズ
4. **互換性** - Django/DRF/Grapheneの標準APIを尊重
