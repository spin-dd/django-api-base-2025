# 用語集

apibaseおよび関連技術の用語集です。

## A

### API (Application Programming Interface)

ソフトウェアコンポーネント間の通信インターフェース。apibaseはREST APIとGraphQL APIの両方をサポート。

### ASGI (Asynchronous Server Gateway Interface)

Pythonの非同期Webアプリケーション用のインターフェース仕様。Django ChannelsはASGIを使用。

## B

### Batch Operation

複数のレコードを一度の操作で処理すること。apibaseは`batch_create`と`batch_update`を提供。

## C

### Channel Layer

Django Channelsでメッセージをルーティングするためのレイヤー。Redis等をバックエンドとして使用。

### Connection (GraphQL)

Relay仕様のページネーション形式。`edges`、`pageInfo`、オプションで`totalCount`を含む。

### Consumer

Django ChannelsでWebSocket接続を処理するクラス。

## D

### DRF (Django REST Framework)

Django用のREST API構築フレームワーク。apibaseの基盤。

## E

### Edge (GraphQL)

Connection内の各要素を表すオブジェクト。`node`と`cursor`を持つ。

### Endpoint

APIのアクセスポイント。URLとHTTPメソッドの組み合わせ。

## F

### Filter

クエリパラメータに基づいてクエリセットを絞り込む機能。apibaseは`BaseFilter`を提供。

### FilterSet

フィルタの集合を定義するクラス。django-filterの概念。

## G

### Global ID (GraphQL)

Relay仕様でオブジェクトを一意に識別するID。Base64エンコードされた`Type:ID`形式。

### Graphene

PythonでGraphQL APIを構築するためのライブラリ。

### GraphQL

APIのクエリ言語。クライアントが必要なデータを指定できる。

## H

### HATEOAS (Hypermedia as the Engine of Application State)

REST APIの設計原則。レスポンスに関連リソースへのリンクを含める。

## M

### Mixin

既存のクラスに機能を追加するためのクラス。例: `DownloadMixin`。

### Mutation (GraphQL)

GraphQLでデータを変更する操作。REST APIのPOST/PUT/PATCH/DELETEに相当。

## N

### Nested Serializer

関連オブジェクトを含むシリアライザ。親オブジェクトと同時に作成・更新可能。

### Node (GraphQL)

Relay仕様でGlobal IDを持つオブジェクトを表すインターフェース。

## P

### Pagination

大量のデータを分割して返す機能。apibaseは`Pagination`クラスを提供。

### Permission

APIへのアクセスを制御する機能。認証と認可を含む。

## Q

### Query (GraphQL)

GraphQLでデータを取得する操作。REST APIのGETに相当。

### QuerySet

Djangoでデータベースクエリを表現するオブジェクト。

## R

### Relay

Facebook製のGraphQLクライアントライブラリ。apibaseはRelay仕様をサポート。

### Renderer

シリアライズされたデータを特定の形式（JSON、CSV等）に変換するクラス。

### Resolver (GraphQL)

GraphQLフィールドの値を解決する関数。

### REST (Representational State Transfer)

Webサービスの設計スタイル。リソース指向、ステートレス。

## S

### Schema (GraphQL)

GraphQL APIの型定義。Query、Mutation、型定義を含む。

### Serializer

Pythonオブジェクトと外部表現（JSON等）を相互変換するクラス。

### Subscription (GraphQL)

GraphQLでリアルタイム更新を受け取る操作。WebSocketを使用。

## U

### URN (Uniform Resource Name)

リソースを永続的に識別するための名前。apibaseの形式: `urn:{app}:{model}:{pk}`

## V

### ViewSet

関連するビューの集合。list、create、retrieve、update、destroyアクションを含む。

## W

### WebSocket

双方向通信を可能にするプロトコル。Django Channelsで使用。

### WordFilter

apibaseが提供する日本語検索対応フィルタ。全角/半角変換、複数キーワードAND検索をサポート。
