import pytest
from django.contrib.auth import get_user_model
from graphene_django.settings import graphene_settings
from graphql import print_schema
from rest_framework.test import APIClient


@pytest.fixture()
def client(db):
    return APIClient()


@pytest.fixture()
def user(db):
    User = get_user_model()
    u, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
    u.set_password("pass")
    u.save()
    return u


def test_sdl_endpoint(client):
    res = client.get("/sdl/")
    assert res.status_code in (200, 403)
    if res.status_code == 200:
        assert b"type Query" in res.content


def test_rest_books_requires_auth(client):
    # Unauthenticated should be forbidden by default
    res = client.get("/api/books/")
    assert res.status_code in (401, 403)


def test_rest_and_graphql_flow(client, user):
    # Force-authenticate as superuser
    client.force_authenticate(user)

    # Create via REST
    res = client.post(
        "/api/books/",
        {"title": "Django 5", "author": "Dev"},
        format="json",
    )
    assert res.status_code in (200, 201), res.content

    # List via REST
    res = client.get("/api/books/")
    assert res.status_code == 200
    data = res.json()
    items = data if isinstance(data, list) else data.get("results", [])
    assert isinstance(items, list) and len(items) >= 1
    assert any(b["title"] == "Django 5" for b in items)

    # Query via GraphQL
    query = """
    query {
      book_set(first: 10) {
        edges { node { title author display urn endpoint } }
      }
    }
    """
    res = client.post("/graphql/", {"query": query}, format="json")
    assert res.status_code == 200
    payload = res.json()
    assert "errors" not in payload
    nodes = [e["node"] for e in payload["data"]["book_set"]["edges"]]
    titles = [n["title"] for n in nodes]
    assert "Django 5" in titles
    # resolvers
    assert any(n["display"].startswith("Django 5") for n in nodes)
    assert any(str(n["urn"]).startswith("urn:") for n in nodes)
    assert any("/api/books/" in str(n["endpoint"]) for n in nodes)

    # Mutation via GraphQL
    mutation = """
    mutation { upsert_book(input: { title: "New Title", author: "A" }) { errors { field messages } title author } }
    """
    res = client.post("/graphql/", {"query": mutation}, format="json")
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("errors") is None
    assert payload["data"]["upsert_book"]["errors"] in (None, [])
    assert payload["data"]["upsert_book"]["title"] == "New Title"


def test_graphql_field_reflection_and_filters(db):
    # Introspect SDL to confirm filter args and fields are exposed
    schema_obj = graphene_settings.SCHEMA
    schema = getattr(schema_obj, "graphql_schema", None) or getattr(schema_obj, "schema", None) or schema_obj
    sdl = print_schema(schema)
    # Node fields
    assert "type BookNode" in sdl
    for f in ("id", "title", "author", "published"):
        assert f in sdl
    assert ("created_at" in sdl) or ("createdAt" in sdl)
    # Filter arguments (from BookFilter)
    for arg in ("title__icontains", "author__icontains", "published__lte", "published__gte"):
        assert arg in sdl


def test_basemodelviewset_batch_endpoints(client, user):
    client.force_authenticate(user)
    # batch_create
    res = client.post(
        "/api/books/batch_create/",
        [
            {"title": "A", "author": "X"},
            {"title": "B", "author": "Y"},
        ],
        format="json",
    )
    assert res.status_code in (200, 201)
    assert isinstance(res.json(), list) and len(res.json()) == 2

    # NOTE: batch_update requires a custom ListSerializer.update implementation; demo omits it.
