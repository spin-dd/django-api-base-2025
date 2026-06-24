# PRD: apibase の identity / optional-dep / nested / authz シームを深化する（候補 1–4）

> 出典: `docs/architecture/architecture-review.html`（2026-06-18, 深さの観点レビュー）。
> 本 PRD は同レビューの候補 **1（アイデンティティ）/ 2（drf-spectacular アダプター）/ 3（ネストリレーション解決の重複排除）/ 4（認可述語の統一）** を 1 つの協調的な深化作業として扱う。
> 候補 5 のうち **死んだ urn パースチェーンの削除のみ** を、候補 1 と同一行で衝突するため Wave 0 の前提作業として取り込む。
>
> フットプリントとシーム、依存関係は実コードに対する並列リーダー＋敵対的レビューで検証済み（行番号は検証時点）。

## Problem Statement（問題 — 利用者の視点）

apibase は DRF と Graphene を同時に拡張するライブラリだが、「1 つの概念」が REST 側と GraphQL 側で**別々に再実装**されている箇所が複数あり、利用者・メンテナにとって次の摩擦を生んでいる。

- **アイデンティティの二重実装。** あるオブジェクトの公開アイデンティティ（`urn` / `endpoint` / `display` と絶対 URI）が、REST の Field（`serializers.py`）と GraphQL の resolver（`graphql/mixins.py`）で二重に計算される。GraphQL は 2 つのヘルパー（`drf_endpoint` / `to_urn`）を借りるためだけに `from .. import serializers` で**表示層が表示層を逆参照**している（レイヤリングの逆転）。urn/endpoint の形式を変えると 2 か所を直す必要がある。
- **optional 依存スタブのドリフト。** `drf-spectacular` の有無を吸収する try/except スタブが `serializers.py` と `viewsets.py` に**個別に存在し、すでに食い違っている**（前者の `OpenApiTypes` は `URI`+`STR`、後者は `STR` のみ／`HAS_DRF_SPECTACULAR` フラグは前者のみで、かつ参照ゼロの死んだフラグ）。`OpenApiTypes` が import 元によって別物になる。
- **ネスト解決規約の重複。** 逆 FK の命名規約（末尾 `_set` 除去 → `get_field`）が `serializers.py` の 2 メソッドに**コピーで存在**し、片方だけ変えると壊れる。
- **認可判定の食い違い。** 「このユーザはこれをして良いか」という 1 つの問いに、`permissions.py` と `viewsets.py` が **4 つの食い違う答え**を持つ（REST は `SAFE_METHODS` を見るが `is_staff` を見ない／GraphQL は `is_staff` を見るが `SAFE_METHODS` を見ない／`check_info` は `PRIVATE` を完全に無視）。下流プロジェクトで「REST では許可、GraphQL では拒否」が偶発的に発生しうる。
- **死んだ urn チェーン。** `endpoint_from_urn → rest_endpoint_from_urn → parse_urn` は呼び出し元ゼロのデッドコードで、アイデンティティ深化の最中に「丁寧に移設」してしまう罠になっている。

これらは小さなライブラリでありながら**ナビゲーション性とテスト容易性**を下げており、特に identity / spectacular / permissions の各面は**振る舞いを守るテストがほぼ無い**（80% 下限を満たさない）。

## Solution（解決 — 利用者の視点）

「1 つの概念は 1 つの深いモジュールが所有し、REST と GraphQL はその上の薄いアダプターになる」という方針で、上記 4 つの面を**集約（移動ではない）**する。

- **候補 1：** 新しい純粋モジュール `ModelIdentity`（例 `apibase/identity.py`）が `urn` / `endpoint` / `display` の計算を所有する。REST の `EndpointField` / `UrnField` / `DisplayField`（表示層に残す）と GraphQL の `resolve_endpoint` / `resolve_urn` / `resolve_display` がそれを呼ぶ薄いアダプターになる。`graphql/mixins.py` の `from .. import serializers` 逆参照辺は消える。
- **候補 2：** `apibase/_spectacular.py` が optional スタブ表面を**一度だけ**定義し、`serializers.py` と `viewsets.py` がそれを import する。死んだ `HAS_DRF_SPECTACULAR` は廃止。
- **候補 3：** `_set` 除去 + `get_field` の解決を**1 つの private 関数**に集約し、2 つの呼び出し元が呼ぶ。戦略レイヤーは導入しない（敵対的レビューで却下済み）。
- **候補 4：** `can(user, perm, *, method, private)` という**純粋述語 1 つ**に判定を統一し、REST（`has_permission`）と GraphQL（`has_query_permission` / `check_info`）が薄いトランスポートアダプターとして委譲する。公開メソッドのシグネチャは下流互換のため維持。

## User Stories

### ライブラリ利用者（下流プロジェクトの開発者）

1. apibase 利用者として、`urn` / `endpoint` の形式を 1 か所変えるだけで REST と GraphQL の両方に反映されてほしい。二重メンテで片方を忘れる事故を避けたいから。
2. apibase 利用者として、同じオブジェクトの `urn` が REST と GraphQL で常に一致してほしい。クライアント側で 2 系統の差異を吸収したくないから。
3. apibase 利用者として、`endpoint` の絶対 URI 化ロジックが各トランスポートで**従来どおりの挙動**を保ってほしい。今動いている下流の出力（相対/絶対）が黙って変わると困るから。
4. apibase 利用者として、`drf-spectacular` をインストールしていてもいなくても `import apibase.serializers` / `import apibase.viewsets` が同じ安定表面で動いてほしい。optional 依存の有無で挙動が割れるのを避けたいから。
5. apibase 利用者として、`drf-spectacular` 未導入でも `OpenApiTypes.URI` を参照する Field（`EndpointField`）が壊れないでほしい。スタブの欠落で import エラーになるのを避けたいから。
6. apibase 利用者として、ネストシリアライザの逆 FK（`*_set`）解決が 1 か所のルールで一貫してほしい。命名規約の重複で予期せぬ差異が出ないように。
7. apibase 利用者として、`NestedOrphanDeleteMixin` の「未指定 vs 空リスト」セマンティクス（PATCH 部分更新）が**従来どおり**保たれてほしい。孤児削除の挙動が静かに壊れると本番データ事故になるから。
8. apibase 利用者として、認可の判定が REST と GraphQL で構造的に一致してほしい。「REST では許可、GraphQL では拒否」の偶発を避けたいから。
9. apibase 利用者として、`PRIVATE` / `SAFE_METHODS` / `is_staff` / `has_perm` の組み合わせ規則が 1 か所で定義されてほしい。下流で `Permission` を継承する際に挙動を予測できるように。
10. apibase 利用者として、`Permission.has_permission` / `has_query_permission` / `check_info` の**シグネチャが変わらない**でほしい。下流の具象サブクラス（例 taihei-cvm-server）が壊れないように。
11. apibase 利用者として、`DownloadMixin` のダウンロード経路に潜在クラッシュバグが無いと確信したい（別途修正・回帰テストを期待）。

### apibase メンテナ

12. メンテナとして、`urn` / `endpoint` / `display` の計算が純粋関数として 1 モジュールに集約され、Field のライフサイクルや resolver 無しで単体テストできてほしい。
13. メンテナとして、`graphql` → `serializers` の逆参照辺が消え、レイヤリングが下向き一方向になってほしい。
14. メンテナとして、optional 依存スタブの定義が 1 ファイルになり、「spectacular の有無で挙動が同じか」を一度だけテストできてほしい。
15. メンテナとして、参照ゼロの `HAS_DRF_SPECTACULAR` フラグと死んだ urn パースチェーンが消えて、表面積が減ってほしい。
16. メンテナとして、`can()` の述語を `user × perm × method × private → bool` のテーブルテストで網羅できてほしい。
17. メンテナとして、identity / spectacular / permissions に特性テスト（characterization tests）が入り、80% 下限に近づいてほしい。

### AI 実装エージェント（ready-for-agent）

18. 実装エージェントとして、候補間の依存関係と並列可否が明示され、どれを直列化しどれを並列化すべきか迷わず着手できてほしい。
19. 実装エージェントとして、候補 1 が候補 5 の死んだ urn チェーン削除と**同一行で衝突する**ことを事前に知り、同一 PR で扱うか順序付けできてほしい。
20. 実装エージェントとして、`build_absolute_uri` の 3 箇所統合が**挙動変更**でありスコープ外だと明記され、リファクタの皮を被った退行を避けられてほしい。
21. 実装エージェントとして、各候補の「触ってよい領域」と「触ってはいけないシーム」（孤児削除 MRO、戦略レイヤー）が明示されてほしい。
22. 実装エージェントとして、各 Wave の完了条件（特性テストが緑、既存テストが緑）が定義されていてほしい。

## Implementation Decisions

### 構築/変更するモジュールとインターフェース

- **候補 1 — ModelIdentity（新規 `apibase/identity.py`）**
  - 公開: `urn`（`model_urn` ベース）、`endpoint`（`drf_endpoint` 相当の純粋計算）、`display`（`str(instance)`）を**純粋関数**として所有。
  - `to_urn(instance, nss, nid)` / `drf_endpoint(instance, url_name, pk_name)` の**シグネチャは厳密に維持**（下流＆ GraphQL の live な呼び出し元のため）。
  - `serializers.py`: `EndpointField` / `UrnField` / `DisplayField` は**表示層に残し**、本体ロジックを `identity` へ委譲する薄いアダプターにする。`from .urn import ...` を整理。
  - `graphql/mixins.py`: `from .. import serializers`（L8 の逆参照）を**削除**し `identity` を import。`resolve_endpoint/urn/display` は `identity` に委譲。`NodeMixin` は `schema.py` 経由で `contrib/schema/query.py`（User/Group/Permission/ContentType）から**生きて使われている**ため、出力互換を保つ。
  - **絶対 URI（`build_absolute_uri`）の 3 箇所統合はやらない（スコープ外）。** 各アダプターは現状のフォールバックを維持する（REST=相対、GraphQL=相対、`urls.py:absolute_path`=絶対）。理由は下記「検証で判明した落とし穴」を参照。

- **候補 2 — `apibase/_spectacular.py`（新規）**
  - 1 つの try/except で**和集合スタブ表面**を定義: `OpenApiTypes{URI, STR}`、`OpenApiParameter{PATH}`、`extend_schema`、`extend_schema_field`。
  - `serializers.py` / `viewsets.py` は当該 try/except ブロックを 1 行の import に置換。**`URI` を含む和集合**であること（intersection ではない）。
  - 死んだ `HAS_DRF_SPECTACULAR` は**廃止**（C5 と重複するため C2 が処分を所有）。

- **候補 3 — ネスト解決の重複排除（`serializers.py` 内）**
  - `_set` 除去 + `_meta.get_field` の解決を**1 つの shared resolver** に集約。現状 `_resolve_nested_related_field` は `NestedOrphanDeleteMixin` 側にあるため、`BaseModelSerializer.update_nested` からも到達できるよう**基底クラス側（またはモジュール関数）へ移設/定義**する（基底はミックスイン専用メソッドに到達できないため、この移設が唯一の構造的ポイント）。
  - **戦略 / `RelationResolver` プロトコルは導入しない**（敵対的レビューで却下）。`update_nested_field` の MRO オーバーライドシーム（孤児削除の第 2 アダプター）には**手を付けない**。

- **候補 4 — `can()` 述語（`permissions.py` 内）**
  - 新規純粋述語 `can(user, perm, *, method=None, private=True) -> bool` が `PRIVATE` / `SAFE_METHODS` / `is_staff` / `has_perm` を 1 か所に統合。
  - `has_permission`（REST）、`has_query_permission` + `check_info`（GraphQL）は `can()` に委譲する**薄いアダプター**にし、**公開シグネチャを維持**。
  - `can()` は `SAFE_METHODS` 判定を `is_safe_method`（`permissions.py:22-23`、`viewsets.py:56` も利用）に**集約**し、3 つ目のコピーを作らない。

- **候補 5（取り込み分）— 死んだ urn チェーン削除**
  - `endpoint_from_urn`（`serializers.py:40-41`）/ `rest_endpoint_from_urn`（`urn.py:29-56`）/ `parse_urn`（`urn.py:20-27`）を削除し、`serializers.py:14` の import から `rest_endpoint_from_urn` を除去（`model_urn` は維持/移設）。**候補 1 と同一行のため同一作業単位で扱う。**

### 依存関係グラフと並列可否（本 PRD の核）

候補は**概念的には独立**だが、**共有ファイルと 1 本のハード依存**により 4 並列はできない。検証済みの辺:

- **ハード（同一作業単位 or 厳密順序）: C5-dead → C1。** 両者が `serializers.py:14` と `urn.py:20-56` の**同一行**を書き換える。
- **ソフト（隣接 / rebase、論理依存ではない）: C2 → C1、C2 → C4、C1 → C3。** 領域は disjoint だがファイル先頭で git の 3 行コンテキストに収まる隣接（`serializers.py:14` は C2 の `16-33` の 1 行隣、`viewsets.py:43` は C2 の `21-37` の 5 行下）。よって **C2 は「並列の兄弟」ではなく「rebase 基点」として先行**させる。
- **C4 は唯一の自由独立**（`permissions.py` を専有。`viewsets.py:43-56` は C2 着地後 disjoint）。

```
Wave 0（地ならし・内部並列可）
  ├─ C2  _spectacular 抽出（HAS_DRF_SPECTACULAR を処分）
  ├─ C5-dead  死んだ urn チェーン削除（serializers.py:14 / urn.py:20-56）
  └─ characterization tests（identity REST+GQL 出力 / spectacular import-smoke / can() 行列）
        ※ C2 と C5-dead は別領域で互いに並列可。HAS_DRF_SPECTACULAR のみ C2 が所有。

Wave 1（本体・C1∥C4 並列）
  ├─ C1  identity（逆参照除去 + ModelIdentity。abs-URI 統合はやらない）
  ├─ C4  authz can() 述語
  └─ C3  ネスト重複排除（C1 と同一ファイルだが >100 行離れた disjoint 領域。C1 と並列 or 直後）

Wave 2（任意・別 PRD）
  └─ build_absolute_uri の統合（特性テストでフォールバックを固定してから）
```

**並列可否のまとめ:**
- 並列可: **C2 ∥ C5-dead**（Wave 0）、**C1 ∥ C4**（Wave 1）。
- 直列必須: **C5-dead → C1**（同一行）、**C2 →（C1, C4）**（先頭隣接・rebase 基点）、**C1 → C3**（同一ファイル・緩い、rebase 前提）。
- **4 つ同時の自由並列は不可。** 実体は「2 本のアームを持つ 2 段パイプライン」。

### 検証で判明した落とし穴（敵対的レビュー）

- **`build_absolute_uri` の 3 箇所統合は挙動変更。** `serializers.py:72`（相対フォールバック）、`graphql/mixins.py:25-26`（相対フォールバック）、`urls.py:15-19 absolute_path`（request 不在時に `https://{get_current_site}{path}` の**絶対**フォールバック）は**意味が異なる**。1 つのヘルパーに畳むと REST/GraphQL の endpoint 出力が相対↔絶対で黙って変わる。テストもほぼ無い。→ **C1 からスコープ外**にし Wave 2 で特性テスト付きで扱う。
- **C1 は本来 C2 に対し論理依存しない**（レビュー意図どおり、装飾された Field クラスは表示層に残すため `identity.py` は `extend_schema_field` を必要としない）。C2 先行は**隣接ハザード回避と置き場の清潔さ**が理由であり、ハードな build gate ではない。

## Testing Decisions

**良いテストの定義:** 公開インターフェース越しの**観測可能な振る舞い**のみを検証し、内部構造（private メソッド名やクラス位置）に結合しない。リファクタで壊れないこと。モックは所有しない境界のみ（DB は実テスト DB を使う）。

- **C1（identity）:** 新 `ModelIdentity` は**純粋関数シーム**としてテスト（`instance + uri-builder → urn/endpoint/display`）。2 つのトランスポートアダプター（DRF `request.build_absolute_uri` / graphene `info.context.build_absolute_uri`）は薄く検証。**現状ガード無し**のため、リファクタ前に urn/endpoint/display の REST/GQL 出力の**特性テストを先に**追加する。
- **C2（spectacular）:** **import-smoke シーム** — `drf-spectacular` 有り/無しの両条件で `import apibase.serializers` / `apibase.viewsets` が成立し、和集合表面（`URI`+`STR`+`OpenApiParameter.PATH`+両デコレーター）が露出することを検証。現状この面のテストは皆無。
- **C3（nested）:** **既存の振る舞いシームを再利用** — `tests/test_nested_orphan_delete.py`（公開 `create()`/`update()` 経由の 7 テスト）が緑のままであること。内部専用テストは増やさない（prior art = 同ファイル）。
- **C4（authz）:** **純粋述語のテーブルテスト** — `can(user, perm, *, method, private)` を `SAFE_METHODS × is_staff × PRIVATE` で網羅。アダプターは公開シグネチャ維持を確認。現状この面のテストは皆無（新規 `tests/test_permissions.py`）。

各 Wave の完了条件: 該当する特性テスト/新規テストが緑、かつ既存スイート（`tests/test_apibase.py`, `tests/test_nested_orphan_delete.py`, `apibase/tests/tests.py`, `apibase/graphql/tests/*`）が緑。

## Out of Scope

- **`build_absolute_uri` の 3 箇所統合**（挙動変更のため。Wave 2 / 別 PRD で特性テスト付きで扱う）。
- **候補 5 の残り（死んだ urn チェーン以外）:** `BatchListSerializer` / `BatchSerializerMixin` の削除、`User.all_permissions` monkey-patch の削除、`action_handlers` / `Action` の削除。
- **却下された大きい抽象化:** `NestedFieldStrategy` / `RelationResolver` プロトコル（C3 の大版）、`WordFilter` / `clone_filter_fields` のビルダー（呼び出し元 1・仮想シーム）。
- **孤児削除の MRO シーム**（`update_nested_field` のオーバーライド連鎖）への変更。

## Further Notes

- **潜在バグ（独立・推奨）:** `DownloadMixin.response_field_data`（`viewsets.py:111-121`）は `create_download_filefield_response(..., format=format)` を呼ぶが `format` はメソッド引数でなく Python ビルトインに解決される。ダウンロード経路にテストが 1 つも無いため未表面化。本 PRD の依存チェーンとは独立に、**回帰テスト付きの小修正**を別途推奨（バグ修正時は再現テスト必須の方針に従う）。
- **第 4 のアイデンティティ表面:** `urls.py` の `absolute_path` / `endpoint` / `endpoint_url` は Wave 2 の abs-URI 統合に関係する。
- **下流互換:** taihei-cvm-server 等の consumer が `Permission` 系・`NodeMixin`・nested serializer を継承する。公開シグネチャ・出力を維持すること。
- **カバレッジ:** identity / spectacular / permissions は現状 80% 下限未達。Wave 0 の特性テストが並列ウェーブの安全網（黙って auto-resolve された merge を検知）。
