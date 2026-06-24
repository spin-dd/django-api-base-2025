"""Tests for `apibase.filters` (FIL-001 BaseFilter id filters, FIL-003 WordFilter)."""

import django_filters
import pytest

from apibase.filters import BaseFilter, WordFilter
from tests.models import Parent

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# FIL-003 WordFilter — Japanese full/half-width aware search
# ---------------------------------------------------------------------------


class _WordFilterSet(django_filters.FilterSet):
    word = WordFilter(lookups=["name"])

    class Meta:
        model = Parent
        fields: list[str] = []


def _names(qs):
    return sorted(p.name for p in qs)


@pytest.mark.parametrize(
    ("stored", "query"),
    [("ＡＢＣ", "ABC"), ("ABC", "ＡＢＣ")],
    ids=["fullwidth-record/halfwidth-query", "halfwidth-record/fullwidth-query"],
)
def test_word_filter_matches_across_width(stored, query):
    # Width normalization is symmetric: a full-width record matches a half-width
    # query and vice versa, because WordFilter ORs zen2han/han2zen of the query.
    Parent.objects.create(name=stored)
    Parent.objects.create(name="ZZZ")

    result = _WordFilterSet({"word": query}, queryset=Parent.objects.all()).qs

    assert _names(result) == [stored]


def test_word_filter_ands_multiple_tokens():
    Parent.objects.create(name="alpha beta")
    Parent.objects.create(name="alpha only")
    Parent.objects.create(name="beta only")

    result = _WordFilterSet({"word": "alpha beta"}, queryset=Parent.objects.all()).qs

    assert _names(result) == ["alpha beta"]


def test_word_filter_splits_on_fullwidth_space():
    Parent.objects.create(name="alpha beta")
    Parent.objects.create(name="alpha only")

    result = _WordFilterSet({"word": "alpha　beta"}, queryset=Parent.objects.all()).qs

    assert _names(result) == ["alpha beta"]


def test_word_filter_empty_value_returns_queryset_unchanged():
    Parent.objects.create(name="alpha")
    Parent.objects.create(name="beta")

    result = _WordFilterSet({"word": ""}, queryset=Parent.objects.all()).qs

    assert _names(result) == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# FIL-001 BaseFilter built-in id filters
# ---------------------------------------------------------------------------


class _ParentFilterSet(BaseFilter):
    class Meta:
        model = Parent
        fields: list[str] = []


@pytest.fixture
def parents():
    return [Parent.objects.create(name=f"p{i}") for i in range(3)]


def test_pk_alias_filters_by_id(parents):
    target = parents[1]

    result = _ParentFilterSet({"pk": target.id}, queryset=Parent.objects.all()).qs

    assert list(result) == [target]


def test_id_includes_filters_to_csv_id_set(parents):
    wanted = [parents[0].id, parents[2].id]

    result = _ParentFilterSet({"id__includes": wanted}, queryset=Parent.objects.all()).qs

    assert sorted(p.id for p in result) == sorted(wanted)


def test_id_excludes_removes_given_ids(parents):
    excluded = [parents[0].id]

    result = _ParentFilterSet({"id__excludes": excluded}, queryset=Parent.objects.all()).qs

    assert sorted(p.id for p in result) == sorted([parents[1].id, parents[2].id])


def test_id_in_csv_accepts_comma_separated_ids(parents):
    csv = f"{parents[0].id},{parents[1].id}"

    result = _ParentFilterSet({"id__in_csv": csv}, queryset=Parent.objects.all()).qs

    assert sorted(p.id for p in result) == sorted([parents[0].id, parents[1].id])


def test_id_not_in_csv_excludes_comma_separated_ids(parents):
    csv = f"{parents[0].id}"

    result = _ParentFilterSet({"id__not_in_csv": csv}, queryset=Parent.objects.all()).qs

    assert sorted(p.id for p in result) == sorted([parents[1].id, parents[2].id])
