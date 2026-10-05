"""Batch updates follow the write database of their selected instances."""

from django.db import IntegrityError
from django.test import override_settings

import pytest
from rest_framework.test import APIRequestFactory

from tests.models import Child, Parent
from tests.routers import InstanceHintWriteRouter
from tests.test_atomic_writes import BatchParentViewSet, NestedBatchParentViewSet


class MixedInstanceWriteRouter(InstanceHintWriteRouter):
    def db_for_write(self, model, **hints):
        instance = hints.get("instance")
        if model is Parent and instance is not None and instance.name == "default target":
            return "default"
        return super().db_for_write(model, **hints)


@pytest.mark.django_db(transaction=True, databases=["default", "nested"])
@pytest.mark.parametrize("routers", [[], ["tests.routers.InstanceHintWriteRouter"]])
def test_later_database_error_rolls_back_updates_on_the_instance_database(routers):
    first = Parent.objects.using("nested").create(name="original first")
    second = Parent.objects.using("nested").create(name="original second")
    request = APIRequestFactory().patch(
        "/parents/batch_update/",
        [{"id": first.pk, "name": "changed first"}, {"id": second.pk, "name": None}],
        format="json",
    )
    with override_settings(DATABASE_ROUTERS=routers), pytest.raises(IntegrityError):
        BatchParentViewSet.as_view({"patch": "batch_update"}, queryset=Parent.objects.using("nested").order_by("id"))(
            request
        )
    assert list(Parent.objects.using("nested").order_by("id").values_list("name", flat=True)) == [
        "original first",
        "original second",
    ]
    assert Parent.objects.using("default").count() == 0


@pytest.mark.django_db(transaction=True, databases=["default", "nested"])
@override_settings(DATABASE_ROUTERS=["tests.routers.InstanceHintWriteRouter"])
def test_later_child_validation_error_restores_all_parents_and_children():
    first = Parent.objects.using("nested").create(name="original first")
    second = Parent.objects.using("nested").create(name="original second")
    first_child = Child.objects.using("nested").create(parent=first, name="original child")
    request = APIRequestFactory().patch(
        "/parents/batch_update/",
        [
            {"id": first.pk, "name": "changed first", "child_set": [{"id": first_child.pk, "name": "changed child"}]},
            {"id": second.pk, "name": "changed second", "child_set": [{"name": "changed second"}]},
        ],
        format="json",
    )
    response = NestedBatchParentViewSet.as_view({"patch": "batch_update"})(request)
    assert response.status_code == 400
    first.refresh_from_db()
    second.refresh_from_db()
    first_child.refresh_from_db()
    assert (first.name, second.name, first_child.name) == ("original first", "original second", "original child")
    assert Child.objects.using("nested").count() == 1


@pytest.mark.django_db(transaction=True, databases=["default", "nested"])
@pytest.mark.parametrize("include_other_database", [True, False])
@override_settings(DATABASE_ROUTERS=["tests.test_batch_write_routing.MixedInstanceWriteRouter"])
def test_only_selected_instances_determine_whether_a_batch_spans_databases(include_other_database):
    first = Parent.objects.using("nested").create(name="nested target")
    second = Parent.objects.using("nested").create(name="default target")
    data = [{"id": first.pk, "name": "changed first"}]
    if include_other_database:
        data.append({"id": second.pk, "name": "changed second"})
    request = APIRequestFactory().patch("/parents/batch_update/", data, format="json")
    response = BatchParentViewSet.as_view({"patch": "batch_update"})(request)
    assert response.status_code == (400 if include_other_database else 200)
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == ("nested target" if include_other_database else "changed first")
    assert second.name == "default target"
    assert Parent.objects.using("default").count() == 0
