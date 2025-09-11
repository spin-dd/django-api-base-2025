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
    created = [Book.objects.create(title=t, author=a, published=p) for t, a, p in items]
    return created


def _results(res):
    data = res.json()
    return data if isinstance(data, list) else data.get("results", [])


def test_exact_and_icontains(client, user, books):
    client.force_authenticate(user)
    # exact by title
    res = client.get("/api/books/", {"title": "Alpha"})
    assert res.status_code == 200
    rows = _results(res)
    assert [r["title"] for r in rows] == ["Alpha"]

    # icontains by author
    res = client.get("/api/books/", {"author__icontains": "dev"})
    assert res.status_code == 200
    rows = _results(res)
    assert all("dev" in r["author"].lower() for r in rows)


def test_gte_lte_date(client, user, books):
    client.force_authenticate(user)
    # published__gte
    res = client.get("/api/books/", {"published__gte": "2024-01-01"})
    assert res.status_code == 200
    rows = _results(res)
    assert all(r["published"] >= "2024-01-01" for r in rows)

    # published__lte
    res = client.get("/api/books/", {"published__lte": "2024-12-31"})
    assert res.status_code == 200
    rows = _results(res)
    assert all(r["published"] <= "2024-12-31" for r in rows)


def test_in_basefilter_variants(client, user, books):
    client.force_authenticate(user)
    ids = [b.id for b in books]
    pick = ids[0:3:2]  # two ids
    csv = ",".join(map(str, pick))

    # id__in (django-filter built-in BaseInFilter)
    res = client.get("/api/books/", {"id__in": csv})
    assert res.status_code == 200
    rows = _results(res)
    assert sorted([r["id"] for r in rows]) == sorted(pick)

    # id__in_csv (apibase BaseIn CSV)
    res = client.get("/api/books/", {"id__in_csv": csv})
    assert res.status_code == 200
    rows = _results(res)
    assert sorted([r["id"] for r in rows]) == sorted(pick)

    # id__not_in_csv
    res = client.get("/api/books/", {"id__not_in_csv": csv})
    assert res.status_code == 200
    rows = _results(res)
    remain = sorted(set(ids) - set(pick))
    assert sorted([r["id"] for r in rows]) == remain

    # id__includes (ListIntegerInFilter) - repeated params
    res = client.get("/api/books/", [("id__includes", str(pick[0])), ("id__includes", str(pick[1]))])
    assert res.status_code == 200
    rows = _results(res)
    assert sorted([r["id"] for r in rows]) == sorted(pick)

    # id__excludes (ListIntegerInFilter, exclude=True)
    res = client.get("/api/books/", [("id__excludes", str(pick[0])), ("id__excludes", str(pick[1]))])
    assert res.status_code == 200
    rows = _results(res)
    assert sorted([r["id"] for r in rows]) == remain


def test_listcharin_and_multiplechoice(client, user, books):
    client.force_authenticate(user)
    # ListCharInFilter (author__in_list) - repeated params
    res = client.get("/api/books/", [("author__in_list", "Dev"), ("author__in_list", "Anon")])
    assert res.status_code == 200
    rows = _results(res)
    assert set(r["author"] for r in rows).issubset({"Dev", "Anon"})

    # MultipleChoiceFilter (author__in_multi) with repeated params
    res = client.get("/api/books/", [("author__in_multi", "Dev"), ("author__in_multi", "Other")])
    assert res.status_code == 200
    rows = _results(res)
    assert set(r["author"] for r in rows).issubset({"Dev", "Other"})
