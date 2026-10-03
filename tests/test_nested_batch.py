"""Each batch record must keep its own nested payload through validation."""

from types import SimpleNamespace

from django.http import QueryDict

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apibase.serializers import BatchListSerializer, BatchSerializerMixin
from tests.models import Child, Parent
from tests.test_atomic_writes import (
    NestedBatchParentSerializer,
    NestedBatchParentViewSet,
    ParentSerializer,
    ParentViewSet,
)
from tests.test_nested_orphan_delete import ParentSerializer as OrphanParentSerializer

pytestmark = pytest.mark.django_db


class NestedParentCreateViewSet(ParentViewSet):
    # Exercise creation through DRF's standard ListSerializer.
    serializer_class = ParentSerializer


def test_batch_create_saves_each_parents_own_children():
    request = APIRequestFactory().post(
        "/parents/batch_create/",
        [
            {"name": "first", "child_set": [{"name": "first child"}, {"name": "extra first child"}]},
            {"name": "second", "child_set": [{"name": "second child"}]},
        ],
        format="json",
    )
    response = NestedParentCreateViewSet.as_view({"post": "batch_create"})(request)

    assert response.status_code == 201
    first, second = Parent.objects.order_by("id")
    assert list(first.child_set.values_list("name", flat=True)) == ["first child", "extra first child"]
    assert list(second.child_set.values_list("name", flat=True)) == ["second child"]


def test_batch_update_saves_each_parents_own_children():
    first = Parent.objects.create(name="original first")
    second = Parent.objects.create(name="original second")
    first_child = Child.objects.create(parent=first, name="original first child")
    second_child = Child.objects.create(parent=second, name="original second child")
    request = APIRequestFactory().patch(
        "/parents/batch_update/",
        [
            {
                "id": first.id,
                "name": "changed first",
                "child_set": [
                    {"id": first_child.id, "name": "changed first child"},
                    {"name": "new first child"},
                ],
            },
            {
                "id": second.id,
                "name": "changed second",
                "child_set": [{"id": second_child.id, "name": "changed second child"}],
            },
        ],
        format="json",
    )
    response = NestedBatchParentViewSet.as_view({"patch": "batch_update"})(request)

    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == "changed first"
    assert second.name == "changed second"
    assert list(first.child_set.values_list("name", flat=True)) == ["changed first child", "new first child"]
    assert list(second.child_set.values_list("name", flat=True)) == ["changed second child"]


def test_querydict_batch_create_saves_each_parents_own_children():
    first_data = QueryDict("name=first", mutable=True)
    first_data.setlist("child_set", [{"name": "first child"}, {"name": "extra first child"}])
    second_data = QueryDict("name=second", mutable=True)
    second_data.setlist("child_set", [{"name": "second child"}])
    serializer = ParentSerializer(data=[first_data, second_data], many=True)
    serializer.is_valid(raise_exception=True)
    first, second = serializer.save()

    assert list(first.child_set.values_list("name", flat=True)) == ["first child", "extra first child"]
    assert list(second.child_set.values_list("name", flat=True)) == ["second child"]


def test_querydict_batch_update_saves_each_parents_own_children():
    first = Parent.objects.create(name="first")
    second = Parent.objects.create(name="second")
    first_child = Child.objects.create(parent=first, name="original first child")
    second_child = Child.objects.create(parent=second, name="original second child")
    first_data = QueryDict(f"id={first.id}", mutable=True)
    first_data.setlist("child_set", [{"id": first_child.id, "name": "changed first child"}])
    second_data = QueryDict(f"id={second.id}", mutable=True)
    second_data.setlist("child_set", [{"id": second_child.id, "name": "changed second child"}])
    serializer = NestedBatchParentSerializer(
        Parent.objects.order_by("id"),
        data=[first_data, second_data],
        many=True,
        partial=True,
        context={"view": SimpleNamespace(request=SimpleNamespace(method="PATCH"))},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    first_child.refresh_from_db()
    second_child.refresh_from_db()
    assert first_child.name == "changed first child"
    assert first_child.parent_id == first.id
    assert second_child.name == "changed second child"
    assert second_child.parent_id == second.id


class OrphanBatchParentSerializer(BatchSerializerMixin, OrphanParentSerializer):
    class Meta(OrphanParentSerializer.Meta):
        list_serializer_class = BatchListSerializer


class OrphanBatchParentViewSet(ParentViewSet):
    serializer_class = OrphanBatchParentSerializer


@pytest.mark.parametrize("cleared_index", [0, 1])
def test_batch_update_distinguishes_omitted_children_from_empty_list(cleared_index):
    parents = [Parent.objects.create(name="first"), Parent.objects.create(name="second")]
    children = [Child.objects.create(parent=parent, name="existing child") for parent in parents]
    payload = [{"id": parent.id, "name": f"updated {parent.name}"} for parent in parents]
    payload[cleared_index]["child_set"] = []
    # QuerySet order differs from input order: nested data must follow the id.
    request = APIRequestFactory().patch("/parents/batch_update/", payload[::-1], format="json")
    response = OrphanBatchParentViewSet.as_view({"patch": "batch_update"})(request)

    assert response.status_code == 200
    for index, parent in enumerate(parents):
        expected = [] if index == cleared_index else [children[index].id]
        assert list(parent.child_set.values_list("id", flat=True)) == expected


class LockedNestedParentSerializer(ParentSerializer):
    def validate(self, attrs):
        # Matches consumers that inspect raw nested input before parent save.
        if any((self._children_set or {}).values()):
            raise ValidationError({"child_set": "Nested changes are locked."})
        return attrs


@pytest.mark.parametrize("querydict_input", [False, True])
def test_single_serializer_validate_can_guard_raw_nested_input(querydict_input):
    if querydict_input:
        data = QueryDict("name=locked", mutable=True)
        data.setlist("child_set", [{"name": "new child"}])
    else:
        data = {"name": "locked", "child_set": [{"name": "new child"}]}
    serializer = LockedNestedParentSerializer(data=data)

    with pytest.raises(ValidationError, match="Nested changes are locked"):
        serializer.is_valid(raise_exception=True)

    assert Parent.objects.count() == 0
    assert Child.objects.count() == 0
