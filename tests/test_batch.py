"""Tests for the batch serializers/endpoint (SER-014, SER-015, VWS-003).

Covers ``BatchSerializerMixin``, ``BatchListSerializer.update``, and the
``batch_update`` endpoint. The mixin reads ``self.context["view"].request.method``,
so serializer-level tests supply a ``SimpleNamespace`` view/request stand-in.
"""

from types import SimpleNamespace
from typing import Any

from django.http import QueryDict

import pytest
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from apibase.serializers import BaseModelSerializer, BatchListSerializer, BatchSerializerMixin
from apibase.viewsets import BaseModelViewSet
from tests.models import BatchItem, Child, NullableBatchItem, Parent
from tests.test_atomic_writes import ParentSerializer

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


class DefaultBatchItemSerializer(BaseModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = BatchItem
        fields = ["id", "name", "code"]
        read_only_fields = ["id"]
        validators = [UniqueTogetherValidator(queryset=BatchItem.objects.all(), fields=["name", "code"])]


class DefaultBatchItemViewSet(BaseModelViewSet):
    queryset = BatchItem.objects.all()
    serializer_class = DefaultBatchItemSerializer


class BatchItemObjectPermission(BasePermission):
    def has_permission(self, request: Any, view: Any) -> bool:
        return not request.data.get("deny_request", False)

    def has_object_permission(self, request: Any, view: Any, obj: BatchItem) -> bool:
        return obj.code != "locked" and not request.data.get("deny_object", False)


class PermissionBatchItemViewSet(DefaultBatchItemViewSet):
    permission_classes = [BatchItemObjectPermission]


class DenyNestedChanges(BasePermission):
    def has_object_permission(self, request: Any, view: Any, obj: Parent) -> bool:
        return "child_set" not in request.data


def test_object_permission_receives_nested_input_before_validation_mutates_it() -> None:
    parent = Parent.objects.create(name="original")
    child = Child.objects.create(parent=parent, name="original child")
    request = APIRequestFactory().patch(
        "/parents/batch_update/",
        [{"id": parent.pk, "name": "changed", "child_set": [{"id": child.pk, "name": "changed child"}]}],
        format="json",
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
    view = ParentBatchViewSet.as_view(
        {"patch": "batch_update"}, serializer_class=ParentSerializer, permission_classes=[DenyNestedChanges]
    )

    response = view(request)

    assert response.status_code == 403, response.data
    parent.refresh_from_db()
    child.refresh_from_db()
    assert (parent.name, child.name) == ("original", "original child")


class CustomReadOnlyIdListSerializer(serializers.ListSerializer):
    def update(self, queryset: Any, validated_data: Any) -> list[Parent]:
        instances = queryset.in_bulk()
        return [
            self.child.update(instances[int(raw["id"])], data)
            for raw, data in zip(self.initial_data, validated_data, strict=True)
        ]


class CustomReadOnlyIdSerializer(BaseModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Parent
        fields = ["id", "name"]
        list_serializer_class = CustomReadOnlyIdListSerializer


class ParentNamePermission(BasePermission):
    def has_object_permission(self, request: Any, view: Any, obj: Parent) -> bool:
        return request.data.get("name") != "forbidden"


@pytest.mark.parametrize("name", ["changed", "forbidden"])
def test_custom_list_update_keeps_read_only_id_support_and_object_permissions(name: str) -> None:
    parent = Parent.objects.create(name="original")
    request = APIRequestFactory().patch(
        "/parents/batch_update/", [{"id": str(parent.pk), "name": name}], format="json"
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True))
    view = ParentBatchViewSet.as_view(
        {"patch": "batch_update"},
        serializer_class=CustomReadOnlyIdSerializer,
        permission_classes=[ParentNamePermission],
    )

    response = view(request)

    assert response.status_code == (403 if name == "forbidden" else 200), response.data
    parent.refresh_from_db()
    assert parent.name == ("original" if name == "forbidden" else name)


@pytest.mark.parametrize("denial", ["object", "deny_request", "deny_object"])
def test_batch_update_checks_every_object_before_saving(denial: str) -> None:
    allowed = BatchItem.objects.create(name="allowed", code="open")
    forbidden = BatchItem.objects.create(name="forbidden", code="locked" if denial == "object" else "other")
    request = APIRequestFactory().patch(
        "/batch-items/batch_update/",
        [{"id": allowed.pk, "name": "changed"}, {"id": forbidden.pk, "name": "changed", denial: True}],
        format="json",
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

    response = PermissionBatchItemViewSet.as_view({"patch": "batch_update"})(request)

    assert response.status_code == 403, response.data
    assert set(BatchItem.objects.values_list("name", flat=True)) == {"allowed", "forbidden"}


def test_default_batch_update_validates_against_each_existing_row() -> None:
    assert DefaultBatchItemSerializer().fields["id"].read_only is True
    first = BatchItem.objects.create(name="first", code="one")
    second = BatchItem.objects.create(name="second", code="two")
    untouched = BatchItem.objects.create(name="untouched", code="three")
    request = APIRequestFactory().patch(
        "/batch-items/batch_update/",
        [{"id": str(first.pk), "name": "first"}, {"id": second.pk, "name": "changed"}],
        format="json",
    )

    response = DefaultBatchItemViewSet.as_view({"patch": "batch_update"})(request)

    assert response.status_code == 200, response.data
    assert set(BatchItem.objects.values_list("name", "code")) == {
        ("first", "one"),
        ("changed", "two"),
        ("untouched", "three"),
    }
    assert {row["id"] for row in response.data} == {first.pk, second.pk}
    untouched.refresh_from_db()
    assert untouched.name == "untouched"


def test_batch_update_rejects_duplicate_rows_from_a_join() -> None:
    parent = Parent.objects.create(name="original")
    Child.objects.create(parent=parent, name="tag-one")
    Child.objects.create(parent=parent, name="tag-two")
    request = APIRequestFactory().patch(
        "/parents/batch_update/", [{"id": parent.pk, "name": "changed"}], format="json"
    )
    view = ParentBatchViewSet.as_view(
        {"patch": "batch_update"}, queryset=Parent.objects.filter(child__name__startswith="tag")
    )

    response = view(request)

    assert response.status_code == 400, response.data
    parent.refresh_from_db()
    assert parent.name == "original"


@pytest.mark.parametrize("conflict", ["existing-row", "duplicate-id", "same-batch"])
def test_default_batch_update_rejects_conflict_without_partial_save(conflict: str) -> None:
    first = BatchItem.objects.create(name="first", code="same")
    second = BatchItem.objects.create(name="second", code="same")
    request = APIRequestFactory().patch(
        "/batch-items/batch_update/",
        [
            {"id": first.pk, "name": "changed"},
            {
                "id": first.pk if conflict == "duplicate-id" else second.pk,
                "name": "changed" if conflict == "same-batch" else "first",
            },
        ],
        format="json",
    )

    response = DefaultBatchItemViewSet.as_view({"patch": "batch_update"})(request)

    assert response.status_code == 400, response.data
    assert set(BatchItem.objects.values_list("name", "code")) == {("first", "same"), ("second", "same")}


class UniqueParentSerializer(BaseModelSerializer):
    name = serializers.CharField(validators=[UniqueValidator(queryset=Parent.objects.all())])

    class Meta:
        model = Parent
        fields = ["id", "name"]


class NullableBatchItemSerializer(BaseModelSerializer):
    class Meta:
        model = NullableBatchItem
        fields = ["id", "name", "code"]


@pytest.mark.parametrize("code", [None, ""], ids=["null-distinct", "blank-is-not-null"])
def test_batch_uniqueness_recheck_keeps_null_values_distinct(code: str | None) -> None:
    rows = [NullableBatchItem.objects.create(name=name, code=None) for name in ("first", "second")]
    request = APIRequestFactory().patch(
        "/batch-items/batch_update/",
        [{"id": row.pk, "name": "changed", "code": code} for row in rows],
        format="json",
    )
    view = BatchItemViewSet.as_view(
        {"patch": "batch_update"},
        queryset=NullableBatchItem.objects.all(),
        serializer_class=NullableBatchItemSerializer,
    )

    response = view(request)

    assert response.status_code == (200 if code is None else 400), response.data
    assert list(NullableBatchItem.objects.values_list("name", "code")) == (
        [("changed", None)] * 2 if code is None else [("first", None), ("second", None)]
    )


def test_batch_update_rechecks_field_uniqueness_between_rows() -> None:
    first = Parent.objects.create(name="first")
    second = Parent.objects.create(name="second")
    request = APIRequestFactory().patch(
        "/parents/batch_update/",
        [{"id": first.pk, "name": "same"}, {"id": second.pk, "name": "same"}],
        format="json",
    )
    view = ParentBatchViewSet.as_view({"patch": "batch_update"}, serializer_class=UniqueParentSerializer)

    response = view(request)

    assert response.status_code == 400, response.data
    assert set(Parent.objects.values_list("name", flat=True)) == {"first", "second"}


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
    with pytest.raises(ValidationError, match="Could not find all objects to update."):
        ser.is_valid(raise_exception=True)


def test_bulk_update_raises_when_id_is_missing_or_falsy():
    p1 = Parent.objects.create(name="orig-1")

    # `id` resolves to a falsy value (0), tripping the `bool(i)` guard in
    # BatchListSerializer.update.
    payload = [
        {"id": p1.id, "name": "updated-1"},
        {"id": 0, "name": "no-id"},
    ]
    ser = _make_batch_serializer(Parent.objects.all(), payload)
    with pytest.raises(ValidationError):
        ser.is_valid(raise_exception=True)


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


@pytest.mark.parametrize("method", ["put", "patch"])
@pytest.mark.parametrize("input_format", ["json", "multipart"], ids=["json", "querydict"])
def test_batch_update_endpoint_rejects_missing_id(method, input_format):
    first = Parent.objects.create(name="original first")
    second = Parent.objects.create(name="original second")
    if input_format == "json":
        payload = [
            {"id": first.id, "name": "changed first"},
            {"name": "changed second"},
        ]
    else:
        # DRF parses an indexed form batch into QueryDict request data.
        payload = QueryDict(mutable=True)
        payload.update({"[0]id": str(first.id), "[0]name": "changed first", "[1]name": "changed second"})

    request = getattr(APIRequestFactory(), method)("/parents/batch_update/", payload, format=input_format)
    action = "batch_update" if method == "patch" else "update_batch"
    response = ParentBatchViewSet.as_view({method: action})(request)

    assert response.status_code == 400
    if input_format == "multipart":
        assert isinstance(response.renderer_context["request"].data, QueryDict)
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == "original first"
    assert second.name == "original second"


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
