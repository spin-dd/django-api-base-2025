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
from tests.models import BatchItem, Parent

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


class ScopedParentBatchViewSet(BaseModelViewSet):
    """Excludes ``hidden-*`` rows so a payload id outside scope is rejected."""

    serializer_class = BatchParentSerializer

    def get_queryset(self):
        return Parent.objects.exclude(name__startswith="hidden")


class BatchItemSerializer(BatchSerializerMixin, BaseModelSerializer):
    class Meta:
        model = BatchItem
        fields = ["id", "name", "code"]
        list_serializer_class = BatchListSerializer


class BatchItemViewSet(BaseModelViewSet):
    queryset = BatchItem.objects.all()
    serializer_class = BatchItemSerializer


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


@pytest.mark.parametrize("stringify", [False, True], ids=["int-id", "str-id"])
def test_to_internal_value_coerces_id_through_field_on_patch(stringify):
    # On PATCH the mixin keeps the lookup id in validated_data, coercing it
    # through the id field. An id arriving as a numeric *string* ("1") must
    # coerce to the int pk so BatchListSerializer.update keys its dict by the
    # same type and the row is genuinely updated (regression for silent no-op).
    p1 = Parent.objects.create(name="orig-1")
    raw_id = str(p1.id) if stringify else p1.id

    ser = _make_batch_serializer(Parent.objects.all(), [{"id": raw_id, "name": "updated-1"}])
    assert ser.is_valid(raise_exception=True)

    assert ser.validated_data[0]["id"] == p1.id
    assert isinstance(ser.validated_data[0]["id"], int)

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


def test_batch_update_rejects_id_outside_filtered_queryset_scope():
    """A payload id outside the viewset's filtered queryset is rejected (VWS-003).

    ``update_batch`` builds the serializer from ``filter_queryset(get_queryset())``;
    an id excluded by ``get_queryset`` must not be updatable, and nothing should
    change.
    """
    in_scope = Parent.objects.create(name="visible-1")
    out_of_scope = Parent.objects.create(name="hidden-1")

    payload = [
        {"id": in_scope.id, "name": "updated-1"},
        {"id": out_of_scope.id, "name": "updated-2"},
    ]
    request = APIRequestFactory().patch("/parents/batch_update/", payload, format="json")
    view = ScopedParentBatchViewSet.as_view({"patch": "batch_update"})
    response = view(request)

    # The out-of-scope id can't be matched, so the whole batch is rejected.
    assert response.status_code == 400

    in_scope.refresh_from_db()
    out_of_scope.refresh_from_db()
    # Neither row changed.
    assert in_scope.name == "visible-1"
    assert out_of_scope.name == "hidden-1"


def test_batch_update_partial_patch_leaves_omitted_field_unchanged():
    """PATCHing only one field of a model with two required writable fields
    must leave the omitted field untouched (regression for dropping partial=True)."""
    item = BatchItem.objects.create(name="orig-name", code="orig-code")

    payload = [{"id": item.id, "name": "updated-name"}]
    request = APIRequestFactory().patch("/batch-items/batch_update/", payload, format="json")
    view = BatchItemViewSet.as_view({"patch": "batch_update"})
    response = view(request)

    assert response.status_code == 200

    item.refresh_from_db()
    assert item.name == "updated-name"
    # The omitted, still-required field is unchanged.
    assert item.code == "orig-code"
