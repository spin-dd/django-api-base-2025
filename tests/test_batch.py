"""Tests for the batch serializers/endpoint (SER-014, SER-015, VWS-003).

Covers ``BatchSerializerMixin``, ``BatchListSerializer.update``, and the
``batch_update`` endpoint. The mixin reads ``self.context["view"].request.method``,
so serializer-level tests supply a ``SimpleNamespace`` view/request stand-in.
"""

from types import SimpleNamespace

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apibase.serializers import BaseModelSerializer, BatchListSerializer, BatchSerializerMixin
from apibase.viewsets import BaseModelViewSet
from tests.models import Parent

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Serializer fixtures
# ---------------------------------------------------------------------------


class BatchParentSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = Parent
        fields = ["id", "name"]
        list_serializer_class = BatchListSerializer


class ParentBatchViewSet(BaseModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = BatchParentSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_context(method="PATCH"):
    """Context shaped as the mixin reads it: ``context["view"].request.method``."""
    return {"view": SimpleNamespace(request=SimpleNamespace(method=method))}


def _make_batch_serializer(instance, data, method="PATCH"):
    return BatchParentSerializer(
        instance=instance,
        data=data,
        many=True,
        partial=True,
        context=_patch_context(method),
    )


# ---------------------------------------------------------------------------
# BatchListSerializer.update — SER-015
# ---------------------------------------------------------------------------


def test_bulk_patch_updates_each_matched_instance_by_id():
    p1 = Parent.objects.create(name="orig-1")
    p2 = Parent.objects.create(name="orig-2")
    p3 = Parent.objects.create(name="orig-3")

    payload = [
        {"id": p1.id, "name": "updated-1"},
        {"id": p2.id, "name": "updated-2"},
    ]
    ser = _make_batch_serializer(Parent.objects.all(), payload)
    assert ser.is_valid(raise_exception=True)
    ser.save()

    p1.refresh_from_db()
    p2.refresh_from_db()
    p3.refresh_from_db()

    assert p1.name == "updated-1"
    assert p2.name == "updated-2"
    # Untouched row keeps its original value.
    assert p3.name == "orig-3"


def test_bulk_update_raises_when_id_not_in_queryset():
    p1 = Parent.objects.create(name="orig-1")
    missing_id = p1.id + 999  # guaranteed not to exist

    payload = [
        {"id": p1.id, "name": "updated-1"},
        {"id": missing_id, "name": "ghost"},
    ]
    ser = _make_batch_serializer(Parent.objects.all(), payload)
    assert ser.is_valid(raise_exception=True)

    with pytest.raises(ValidationError, match="Could not find all objects to update."):
        ser.save()


def test_bulk_update_raises_when_id_is_missing_or_falsy():
    p1 = Parent.objects.create(name="orig-1")

    # `id` resolves to a falsy value (0), tripping the `bool(i)` guard in
    # BatchListSerializer.update.
    payload = [
        {"id": p1.id, "name": "updated-1"},
        {"id": 0, "name": "no-id"},
    ]
    ser = _make_batch_serializer(Parent.objects.all(), payload)
    assert ser.is_valid(raise_exception=True)

    with pytest.raises(ValidationError):
        ser.save()


# ---------------------------------------------------------------------------
# BatchSerializerMixin.to_internal_value — SER-014
# ---------------------------------------------------------------------------


def test_to_internal_value_preserves_id_under_lookup_field_on_patch():
    # The mixin keeps the lookup id in validated_data on PATCH, taken straight
    # from the raw payload (not re-coerced), so an int id round-trips into update.
    p1 = Parent.objects.create(name="orig-1")

    payload = [{"id": p1.id, "name": "updated-1"}]
    ser = _make_batch_serializer(Parent.objects.all(), payload)
    assert ser.is_valid(raise_exception=True)

    assert ser.validated_data[0]["id"] == p1.id

    # And the round-trip update keyed by that id succeeds.
    ser.save()
    p1.refresh_from_db()
    assert p1.name == "updated-1"


# ---------------------------------------------------------------------------
# BaseModelViewSet.batch_update endpoint — VWS-003
# ---------------------------------------------------------------------------


def test_batch_update_endpoint_updates_records_by_id():
    """PATCH /batch_update drives the batch serializer end-to-end via a real request."""
    p1 = Parent.objects.create(name="orig-1")
    p2 = Parent.objects.create(name="orig-2")

    payload = [
        {"id": p1.id, "name": "updated-1"},
        {"id": p2.id, "name": "updated-2"},
    ]
    request = APIRequestFactory().patch("/parents/batch_update/", payload, format="json")
    view = ParentBatchViewSet.as_view({"patch": "batch_update"})
    response = view(request)

    assert response.status_code == 200

    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.name == "updated-1"
    assert p2.name == "updated-2"
