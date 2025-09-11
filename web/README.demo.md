Quick start for the Django 5 demo site

- Sync deps (once):
  - `uv sync --group dev`

- Migrate DB and create a superuser:
  - `uv run python web/manage.py migrate`
  - `uv run python web/manage.py createsuperuser`

- Run dev server:
  - `uv run python web/manage.py runserver 8000`

Endpoints
- REST: `GET/POST /api/books/` (auth required; Basic or session)
- GraphQL: `/graphql/` (GraphiQL available; auth required)
- SDL: `/sdl/`

Sample GraphQL
mutation {
  upsert_book(input: {title: "Django 5", author: "Adrian"}) { clientMutationId }
}

query {
  book_set(first: 10, title__icontains: "Django") {
    edges { node { id pk title author endpoint urn display } }
    totalCount
    records
  }
}
