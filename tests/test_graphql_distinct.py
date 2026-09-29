"""GraphQL の一覧に `DISTINCT` を足すかを、組み上がったクエリで決める.

`method` を持つフィルタでは、django-filter は `field_name` を method へ渡すだけで
lookup を組まない。`field_name` が多値リレーションを跨いでいても、method が
`EXISTS` やサブクエリで評価すれば行は増えず、JOIN を張れば増える。
"""

from django.db.models import Exists, OuterRef

import django_filters
import pytest

from apibase.graphql.fields import _needs_distinct, _queryset_has_duplicating_joins
from tests.models import Vendor, VendorNote, VendorTag


class _VendorMethodFilter(django_filters.FilterSet):
    tag_exists = django_filters.CharFilter(field_name="tags__name", method="filter_tag_exists")
    tag_joined = django_filters.CharFilter(field_name="tags__name", method="filter_tag_joined")
    note_joined = django_filters.CharFilter(method="filter_note_joined")

    class Meta:
        model = Vendor
        fields = []

    def filter_tag_exists(self, queryset, name, value):
        return queryset.filter(Exists(VendorTag.objects.filter(vendor=OuterRef("pk"), name=value)))

    def filter_tag_joined(self, queryset, name, value):
        return queryset.filter(**{name: value})

    def filter_note_joined(self, queryset, name, value):
        return queryset.filter(notes__text=value)


def _resolve(data):
    """`NodeSet.resolve_queryset` と同じ判定で、一覧が返す行."""
    qs = _VendorMethodFilter(data, queryset=Vendor.all_objects.all()).qs
    needs_distinct = _needs_distinct(qs, data, _VendorMethodFilter)
    return needs_distinct, list(qs.distinct() if needs_distinct else qs)


@pytest.fixture
def vendor():
    """同じ名前のタグとメモを 2 件ずつ持つ取引先 (JOIN すると 2 行になる)."""
    vendor = Vendor.all_objects.create(name="v")
    VendorTag.objects.create(vendor=vendor, name="a")
    VendorTag.objects.create(vendor=vendor, name="a")
    VendorNote.objects.create(content_object=vendor, text="n")
    VendorNote.objects.create(content_object=vendor, text="n")
    return vendor


@pytest.mark.django_db
def test_method_filter_evaluating_the_relation_in_a_subquery_skips_distinct(vendor):
    """`field_name` が逆参照を跨いでも、method が JOIN しなければ `DISTINCT` を足さない."""
    assert _resolve({"tag_exists": "a"}) == (False, [vendor])


@pytest.mark.django_db
def test_method_filter_joining_the_relation_keeps_distinct(vendor):
    """method が逆参照を JOIN すれば、行が増えるので `DISTINCT` を足す."""
    assert _resolve({"tag_joined": "a"}) == (True, [vendor])


@pytest.mark.django_db
def test_method_filter_joining_a_generic_relation_keeps_distinct(vendor):
    """GenericRelation の JOIN も行を増やすので `DISTINCT` を足す."""
    assert _resolve({"note_joined": "n"}) == (True, [vendor])


def test_generic_relation_join_counts_as_duplicating():
    """`GenericRel` は多重度を many-to-one と名乗るが、JOIN すると逆参照と同じく行が増える."""
    assert _queryset_has_duplicating_joins(Vendor.all_objects.filter(notes__text="n")) is True
