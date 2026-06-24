# GraphQL設計思想

apibaseのGraphQL API設計思想について説明します。

## 設計原則

### 1. 型安全性

すべてのデータは厳密に型定義されます。

```graphql
type Book {
    id: ID!
    title: String!
    price: Int!
    author: Author!
    publishedDate: Date
}
```

### 2. クライアント駆動

クライアントが必要なデータのみを要求できます。

```graphql
# 必要なフィールドのみ取得
query {
    books {
        id
        title
    }
}

# 関連データも同時に取得
query {
    books {
        id
        title
        author {
            name
        }
    }
}
```

### 3. 単一エンドポイント

すべてのクエリは単一のエンドポイントで処理されます。

```
POST /graphql/
```

## Query設計

### リスト取得

```graphql
type Query {
    # シンプルなリスト
    books: [Book!]!

    # フィルタリング対応
    books(
        search: String
        authorId: ID
        isAvailable: Boolean
    ): [Book!]!

    # ページネーション対応（Relay）
    books(
        first: Int
        after: String
        last: Int
        before: String
    ): BookConnection!
}
```

### 単一取得

```graphql
type Query {
    # IDで取得
    book(id: ID!): Book

    # Relay Node
    node(id: ID!): Node
}
```

## Mutation設計

### 作成

```graphql
type Mutation {
    createBook(input: CreateBookInput!): CreateBookPayload!
}

input CreateBookInput {
    title: String!
    authorId: ID!
    price: Int!
}

type CreateBookPayload {
    book: Book
    ok: Boolean!
    errors: [String!]
}
```

### 更新

```graphql
type Mutation {
    updateBook(id: ID!, input: UpdateBookInput!): UpdateBookPayload!
}

input UpdateBookInput {
    title: String
    price: Int
}
```

### 削除

```graphql
type Mutation {
    deleteBook(id: ID!): DeleteBookPayload!
}

type DeleteBookPayload {
    ok: Boolean!
}
```

## Relay仕様

### Node Interface

```graphql
interface Node {
    id: ID!
}

type Book implements Node {
    id: ID!
    title: String!
}
```

### Connection

```graphql
type BookConnection {
    edges: [BookEdge!]!
    pageInfo: PageInfo!
    totalCount: Int
}

type BookEdge {
    node: Book!
    cursor: String!
}

type PageInfo {
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
}
```

### Global ID

```graphql
# Base64エンコードされたID
# "Qm9vazox" → "Book:1"
query {
    node(id: "Qm9vazox") {
        ... on Book {
            title
        }
    }
}
```

## エラーハンドリング

### フィールドレベルエラー

```json
{
    "data": {
        "createBook": {
            "book": null,
            "ok": false,
            "errors": ["タイトルは必須です"]
        }
    }
}
```

### クエリレベルエラー

```json
{
    "data": null,
    "errors": [
        {
            "message": "認証が必要です",
            "locations": [{"line": 1, "column": 1}],
            "path": ["books"]
        }
    ]
}
```

## 認証・認可

### コンテキストからユーザー取得

```python
def resolve_my_books(self, info):
    user = info.context.user
    if not user.is_authenticated:
        raise Exception("認証が必要です")
    return Book.objects.filter(owner=user)
```

### 型レベルのフィルタリング

```python
class BookType(DjangoObjectType):
    @classmethod
    def get_queryset(cls, queryset, info):
        if not info.context.user.is_staff:
            return queryset.filter(is_published=True)
        return queryset
```

## N+1問題の対策

### select_related / prefetch_related

```python
def resolve_books(self, info):
    return Book.objects.select_related('author').prefetch_related('tags')
```

### DataLoader

```python
from promise import Promise
from promise.dataloader import DataLoader

class AuthorLoader(DataLoader):
    def batch_load_fn(self, author_ids):
        authors = {a.id: a for a in Author.objects.filter(id__in=author_ids)}
        return Promise.resolve([authors.get(id) for id in author_ids])
```
