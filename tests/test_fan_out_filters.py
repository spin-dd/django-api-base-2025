"""Regression tests for opt-in fan-out relation folding."""

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.http import QueryDict

import pytest

from apibase.contrib.schema.filters import GroupFilter, UserFilter
from apibase.filters import (
    BaseFilter,
    FanOutBaseFilter,
    FanOutCharFilter,
    FanOutDateFromToRangeFilter,
    FanOutFilterMixin,
    FanOutModelChoiceFilter,
    FanOutModelMultipleChoiceFilter,
    FanOutWordFilter,
)

pytestmark = pytest.mark.django_db


class _DefaultUserFilter(BaseFilter):
    class Meta:
        model = User
        fields = ["groups"]


class _FanOutUserFilter(FanOutBaseFilter):
    class Meta:
        model = User
        fields = ["groups"]


def _group_query(*groups):
    query = QueryDict(mutable=True)
    query.setlist("groups", [str(group.pk) for group in groups])
    return query


def _permission_query(*permissions):
    query = QueryDict(mutable=True)
    query.setlist("permissions", [str(permission.pk) for permission in permissions])
    return query


def _user_permission_query(*permissions):
    query = QueryDict(mutable=True)
    query.setlist("user_permissions", [str(permission.pk) for permission in permissions])
    return query


def _permissions():
    content_type = ContentType.objects.get_for_model(User)
    return (
        Permission.objects.create(name="first", codename="fan_out_first", content_type=content_type),
        Permission.objects.create(name="second", codename="fan_out_second", content_type=content_type),
    )


def test_fan_out_base_filter_folds_a_multi_value_relation_without_outer_distinct():
    """The opt-in filter returns each parent once without outer DISTINCT."""
    first = Group.objects.create(name="first")
    second = Group.objects.create(name="second")
    user = User.objects.create(username="target")
    user.groups.set([first, second])

    default = _DefaultUserFilter(_group_query(first, second), queryset=User.objects.all()).qs
    folded = _FanOutUserFilter(_group_query(first, second), queryset=User.objects.all()).qs

    assert default.query.distinct is True
    assert list(folded.values_list("pk", flat=True)) == [user.pk]
    assert folded.query.distinct is False
    assert " IN (SELECT " in str(folded.query).upper()


@pytest.mark.parametrize(
    "filter_class",
    [
        FanOutCharFilter,
        FanOutWordFilter,
        FanOutModelChoiceFilter,
        FanOutModelMultipleChoiceFilter,
        FanOutDateFromToRangeFilter,
    ],
)
def test_named_fan_out_filters_share_the_public_folding_contract(filter_class):
    assert issubclass(filter_class, FanOutFilterMixin)


@pytest.mark.parametrize("query", [QueryDict(), QueryDict("groups=")])
def test_fan_out_base_filter_leaves_an_unfiltered_queryset_unchanged(query):
    base = User.objects.order_by("username")

    filtered = _FanOutUserFilter(query, queryset=base).qs

    assert str(filtered.query) == str(base.query)


def test_contrib_user_groups_uses_the_opt_in_fan_out_filter():
    """The shipped auth User filter uses the inexpensive folding path."""
    first = Group.objects.create(name="first")
    second = Group.objects.create(name="second")
    user = User.objects.create(username="target")
    user.groups.set([first, second])

    filtered = UserFilter(_group_query(first, second), queryset=User.objects.all()).qs

    assert list(filtered.values_list("pk", flat=True)) == [user.pk]
    assert filtered.query.distinct is False
    assert " IN (SELECT " in str(filtered.query).upper()


def test_contrib_user_permissions_uses_the_opt_in_fan_out_filter():
    """The other generated User M2M filter follows the same public contract."""
    first, second = _permissions()
    user = User.objects.create(username="target")
    user.user_permissions.set([first, second])

    filtered = UserFilter(_user_permission_query(first, second), queryset=User.objects.all()).qs

    assert list(filtered.values_list("pk", flat=True)) == [user.pk]
    assert filtered.query.distinct is False
    assert " IN (SELECT " in str(filtered.query).upper()


def test_contrib_group_permissions_uses_the_opt_in_fan_out_filter():
    """The shipped auth Group filter opts into the same folding behavior."""
    first, second = _permissions()
    group = Group.objects.create(name="target")
    group.permissions.set([first, second])

    filtered = GroupFilter(_permission_query(first, second), queryset=Group.objects.all()).qs

    assert list(filtered.values_list("pk", flat=True)) == [group.pk]
    assert filtered.query.distinct is False
    assert " IN (SELECT " in str(filtered.query).upper()
