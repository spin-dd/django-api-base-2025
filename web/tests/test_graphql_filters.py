import datetime as dt

import pytest
from django.contrib.auth import get_user_model
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


@pytest.fixture()
def books(db):
    from web.demo.models import Book

    Book.objects.all().delete()
    items = [
        ("Alpha", "Dev", dt.date(2023, 12, 31)),
        ("Beta", "Anon", dt.date(2024, 1, 1)),
        ("Gamma", "Other", dt.date(2024, 6, 15)),
        ("Delta", "Dev", dt.date(2025, 1, 1)),
        ("Epsilon", "Anon", dt.date(2025, 6, 1)),
    ]
    return [Book.objects.create(title=t, author=a, published=p) for t, a, p in items]


def _gql(client: APIClient, query: str, variables=None):
    res = client.post("/graphql/", {"query": query, "variables": variables or {}}, format="json")
    assert res.status_code == 200, res.content
    payload = res.json()
    assert "errors" not in payload, payload.get("errors")
    return payload["data"]


def _ids_from_edges(payload):
    return [int(e["node"]["pk"]) for e in payload["book_set"]["edges"]]


def test_graphql_filters_basic(client, user, books):
    client.force_authenticate(user)

    query = """
    query($text: String, $gte: Date, $lte: Date) {
      book_set(first: 50, title__icontains: $text, published__gte: $gte, published__lte: $lte) {
        edges { node { id title author published } }
      }
    }
    """
    data = _gql(
        client,
        query,
        variables={"text": "a", "gte": "2024-01-01", "lte": "2024-12-31"},
    )
    titles = [e["node"]["title"].lower() for e in data["book_set"]["edges"]]
    assert all("a" in t for t in titles)


def test_graphql_filters_in_variants(client, user, books):
    client.force_authenticate(user)
    ids = [b.id for b in books]
    pick = ids[0:3:2]  # two ids
    csv = ",".join(map(str, pick))

    # id__in_csv (CSV include)
    query_in_csv = """
    query($csv: String) {
      book_set(first: 50, id__in_csv: $csv) { edges { node { pk } } }
    }
    """
    data = _gql(client, query_in_csv, variables={"csv": csv})
    assert sorted(_ids_from_edges(data)) == sorted(pick)

    # id_NotInCsv (apibase BaseIn CSV)
    query_not_in_csv = """
    query($csv: String) {
      book_set(first: 50, id__not_in_csv: $csv) { edges { node { pk } } }
    }
    """
    data = _gql(client, query_not_in_csv, variables={"csv": csv})
    remain = sorted(set(ids) - set(pick))
    assert sorted(_ids_from_edges(data)) == remain

    # id_Includes (ListIntegerInFilter) - list argument
    query_includes = """
    query($ids: [Int!]) {
      book_set(first: 50, id__includes: $ids) { edges { node { pk } } }
    }
    """
    data = _gql(client, query_includes, variables={"ids": pick})
    assert sorted(_ids_from_edges(data)) == sorted(pick)

    # id_Excludes (ListIntegerInFilter, exclude=True)
    query_excludes = """
    query($ids: [Int!]) {
      book_set(first: 50, id__excludes: $ids) { edges { node { pk } } }
    }
    """
    data = _gql(client, query_excludes, variables={"ids": pick})
    assert sorted(_ids_from_edges(data)) == remain

    # author_InList (ListCharInFilter) - list argument
    query_author_in = """
    query($names: [String!]) {
      book_set(first: 50, author__in_list: $names) { edges { node { author } } }
    }
    """
    data = _gql(client, query_author_in, variables={"names": ["Dev", "Anon"]})
    authors = set(e["node"]["author"] for e in data["book_set"]["edges"])
    assert authors.issubset({"Dev", "Anon"})

    # author_InMulti (MultipleChoiceFilter) - list argument
    query_author_multi = """
    query($names: [String!]) {
      book_set(first: 50, author__in_multi: $names) { edges { node { author } } }
    }
    """
    data = _gql(client, query_author_multi, variables={"names": ["Dev", "Other"]})
    authors = set(e["node"]["author"] for e in data["book_set"]["edges"])
    assert authors.issubset({"Dev", "Other"})
