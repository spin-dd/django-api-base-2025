"""Tests for `apibase.filters` (FIL-001 BaseFilter id filters, FIL-003 WordFilter,
FIL-009 clone_filter_fields)."""

from django.http import QueryDict

import django_filters
import pytest

from apibase.filters import (
    BaseFilter,
    ListCharInFilter,
    RelatedFilterSetMixin,
    WordFilter,
    clone_filter_fields,
    make_related_filterset,
    validate_method_filters,
)
from tests.models import Child, Parent

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


class _NameInFilterSet(BaseFilter):
    name__in = ListCharInFilter(field_name="name")

    class Meta:
        model = Parent
        fields: list[str] = []


def _name_in_qs(query_string, queryset):
    return _NameInFilterSet(QueryDict(query_string), queryset=queryset).qs


def test_list_in_filter_blank_value_does_not_filter():
    # A cleared multi-select still sends the key with no value. Before the empty-member
    # drop this filtered on `name__in=[""]`, so the caller silently got only the blank
    # rows back instead of the unfiltered set -- with a valid form and no error.
    kept = Parent.objects.create(name="p0")
    blank = Parent.objects.create(name="")

    result = _name_in_qs("name__in=", Parent.objects.all())

    assert sorted(p.id for p in result) == sorted([kept.id, blank.id])


def test_list_in_filter_ignores_blank_alongside_real_values():
    kept = Parent.objects.create(name="p0")
    Parent.objects.create(name="p1")
    Parent.objects.create(name="")

    result = _name_in_qs("name__in=&name__in=p0", Parent.objects.all())

    assert [p.id for p in result] == [kept.id]


def test_id_in_csv_accepts_comma_separated_ids(parents):
    csv = f"{parents[0].id},{parents[1].id}"

    result = _ParentFilterSet({"id__in_csv": csv}, queryset=Parent.objects.all()).qs

    assert sorted(p.id for p in result) == sorted([parents[0].id, parents[1].id])


def test_id_not_in_csv_excludes_comma_separated_ids(parents):
    csv = f"{parents[0].id}"

    result = _ParentFilterSet({"id__not_in_csv": csv}, queryset=Parent.objects.all()).qs

    assert sorted(p.id for p in result) == sorted([parents[1].id, parents[2].id])


# ---------------------------------------------------------------------------
# FIL-009 clone_filter_fields — scoping (fields / exclude)
# ---------------------------------------------------------------------------


class _CloneSourceFilter(BaseFilter):
    """Source filterset, cloned onto ``Child`` under the ``parent`` prefix."""

    name__contains = django_filters.CharFilter(field_name="name", lookup_expr="contains")
    named_like = django_filters.CharFilter(method="filter_named_like")

    class Meta:
        model = Parent
        fields: list[str] = []

    def filter_named_like(self, queryset, name, value):
        return queryset.filter(**{f"{name}__contains": value})


def test_clone_filter_fields_clones_every_filter_by_default():
    cloned = clone_filter_fields(_CloneSourceFilter, "parent")

    assert "parent__name__contains" in cloned
    assert "parent__pk" in cloned
    assert cloned["parent__name__contains"].field_name == "parent__name"


def test_clone_filter_fields_keeps_declared_filters_before_generated_ones():
    # The clone's order is the order the filters are applied in, so it follows the
    # source's "declared, then generated" order rather than ``base_filters`` order
    # (django-filter puts Meta-generated filters first there).
    class _OrderProbeFilter(BaseFilter):
        zzz__contains = django_filters.CharFilter(field_name="name", lookup_expr="contains")

        class Meta:
            model = Parent
            fields = ["name"]

    cloned = list(clone_filter_fields(_OrderProbeFilter, "parent"))

    assert cloned.index("parent__zzz__contains") < cloned.index("parent__name")


def test_clone_filter_fields_fields_limits_the_cloned_set():
    cloned = clone_filter_fields(_CloneSourceFilter, "parent", fields=["name__contains"])

    assert set(cloned) == {"parent__name__contains"}


def test_clone_filter_fields_exclude_drops_named_filters():
    cloned = clone_filter_fields(_CloneSourceFilter, "parent", exclude=["name__contains"])

    assert "parent__name__contains" not in cloned
    assert "parent__pk" in cloned


def test_clone_filter_fields_rejects_fields_and_exclude_together():
    with pytest.raises(TypeError):
        clone_filter_fields(_CloneSourceFilter, "parent", fields=["name__contains"], exclude=["pk"])


@pytest.mark.parametrize("kwarg", ["fields", "exclude"])
def test_clone_filter_fields_rejects_unknown_names(kwarg):
    # A typo must not silently widen (fields) or silently no-op (exclude) the clone.
    with pytest.raises(ValueError, match="no_such_filter"):
        clone_filter_fields(_CloneSourceFilter, "parent", **{kwarg: ["no_such_filter"]})


# ---------------------------------------------------------------------------
# FIL-009 clone_filter_fields — string ``method`` handling
# ---------------------------------------------------------------------------


def _child_filterset(fields):
    meta = type("Meta", (), {"model": Child, "fields": []})
    return type("_ClonedChildFilter", (django_filters.FilterSet,), {**fields, "Meta": meta})


def test_cloned_string_method_stays_unresolved_until_query_time():
    # The trap this helper sets: declaring the clone is silent, and the failure
    # lands on whoever first uses the query parameter.
    cloned = _child_filterset(clone_filter_fields(_CloneSourceFilter, "parent"))

    with pytest.raises(AssertionError, match="filter_named_like"):
        _ = cloned({"parent__named_like": "x"}, queryset=Child.objects.all()).qs


def test_validate_method_filters_reports_unresolvable_methods():
    cloned = _child_filterset(clone_filter_fields(_CloneSourceFilter, "parent"))

    assert validate_method_filters(cloned) == [("parent__named_like", "filter_named_like")]


def test_validate_method_filters_passes_when_the_method_resolves():
    assert validate_method_filters(_CloneSourceFilter) == []


def test_clone_filter_fields_methods_drop_skips_string_method_filters():
    cloned = clone_filter_fields(_CloneSourceFilter, "parent", methods="drop")

    assert "parent__named_like" not in cloned
    assert "parent__name__contains" in cloned


def test_clone_filter_fields_methods_error_names_the_offending_filters():
    with pytest.raises(ValueError, match="named_like"):
        clone_filter_fields(_CloneSourceFilter, "parent", methods="error")


def test_clone_filter_fields_rejects_unknown_method_policy():
    with pytest.raises(ValueError, match="methods"):
        clone_filter_fields(_CloneSourceFilter, "parent", methods="maybe")


def test_clone_filter_fields_keeps_callable_methods_under_every_policy():
    # A callable ``method`` needs no lookup on the parent, so it is not what the
    # policy is about.
    class _CallableMethodFilter(BaseFilter):
        named_like = django_filters.CharFilter(method=lambda qs, name, value: qs)

        class Meta:
            model = Parent
            fields: list[str] = []

    cloned = clone_filter_fields(_CallableMethodFilter, "parent", methods="drop")

    assert "parent__named_like" in cloned


def test_make_related_filterset_forwards_the_method_policy():
    related = make_related_filterset("_Related", methods="drop", parent=_CloneSourceFilter)

    assert "parent__named_like" not in related.base_filters
    assert "parent__name__contains" in related.base_filters


def test_create_related_filterset_forwards_scoping_and_method_policy():
    class _MixedSourceFilter(RelatedFilterSetMixin, _CloneSourceFilter):
        class Meta:
            model = Parent
            fields: list[str] = []

    related = _MixedSourceFilter.create_related_filterset("parent", methods="drop")

    assert "parent__named_like" not in related.base_filters
    assert validate_method_filters(related) == []
