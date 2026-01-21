# 設計判断

apibaseの技術的な設計判断について説明します。

## ViewSet設計

### BaseModelViewSetにDownloadMixinを含める理由

**判断**: `DownloadMixin`を`BaseModelViewSet`に組み込む

**理由**:
- FileFieldを持つモデルは一般的
- ダウンロード機能は汎用的
- 明示的に除外するより含める方が便利

**代替案**:
- 別途`DownloadableModelViewSet`を提供
- 利用者が明示的にミックスインを追加

---

### バッチ操作をViewSetに組み込む理由

**判断**: `batch_create`と`batch_update`アクションを標準で提供

**理由**:
- 一括操作の需要が高い
- 個別実装は冗長になりがち
- パフォーマンス最適化が可能

**トレードオフ**:
- 不要な場合でもエンドポイントが存在する
- カスタマイズが必要な場合がある

## Serializer設計

### endpoint/urn/displayフィールドを標準で含める理由

**判断**: これらのメタフィールドをデフォルトで提供

**理由**:
- クライアントがリソースを識別しやすい
- HATEOAS原則に従う
- 一貫したAPI設計が可能

**代替案**:
- 必要な場合のみ明示的に追加
- 設定で有効/無効を切り替え

---

### ネストシリアライザの実装方法

**判断**: `nested_fields`属性で指定、`update_or_create`パターンを使用

**理由**:
- 明示的で理解しやすい
- 更新と作成を統一的に扱える
- 既存のDRFパターンと整合性がある

**トレードオフ**:
- 複雑なネスト構造では設定が増える
- パフォーマンスへの影響

## Filter設計

### WordFilterの全角/半角対応

**判断**: jaconvを使用して全角/半角両方で検索

**理由**:
- 日本語検索では全角/半角の違いが問題になる
- ユーザーは入力形式を意識したくない
- 検索精度が向上する

**トレードオフ**:
- クエリが2倍になる
- パフォーマンスへの影響

---

### BaseFilterにid__includes等を組み込む理由

**判断**: 汎用的なIDフィルタを標準で提供

**理由**:
- IDによる一括操作は頻繁に必要
- すべてのモデルに適用可能
- 一貫したAPIを提供

## GraphQL設計

### Relay仕様への対応

**判断**: Relay仕様（Node, Connection）をサポート

**理由**:
- Relayクライアントとの互換性
- ページネーションの標準化
- Global IDによる統一的なリソースアクセス

**代替案**:
- シンプルなリスト返却のみ
- 独自のページネーション形式

---

### DRFシリアライザとGraphQL型の分離

**判断**: それぞれ独立して定義

**理由**:
- 用途が異なる（シリアライズ vs 型定義）
- 柔軟性を維持
- 既存のパターンに従う

**代替案**:
- 統一的なスキーマ定義から両方を生成
- SerializerMutationのような統合

## 設定設計

### apibase_settingsの使用

**判断**: 専用の設定オブジェクトを提供

**理由**:
- Django設定との分離
- デフォルト値の管理が容易
- 型安全性の向上

**実装**:
```python
APIBASE = {
    'STORAGE_PREFIX': 'files',
}
```

## 依存関係

### オプション依存関係の扱い

**判断**: drf-spectacularなどをオプション依存として扱う

**理由**:
- コアライブラリをスリムに保つ
- 不要な依存関係を避ける
- インストールの柔軟性

**実装**:
```python
try:
    from drf_spectacular.utils import extend_schema
except ImportError:
    def extend_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
```

## 将来の方向性

### 検討中の改善

1. **非同期対応**: Django 4.1+のasync viewサポート
2. **型ヒント強化**: PEP 604スタイルの型ヒント
3. **OpenAPI 3.1対応**: 最新仕様への対応
4. **GraphQL Subscription**: WebSocketベースのリアルタイム更新
