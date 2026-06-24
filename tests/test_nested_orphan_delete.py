"""Tests for `NestedOrphanDeleteMixin`.

Verifies the behaviour matrix:

  payload state              -> orphan-delete action
  -------------------------------------------------
  field absent from payload  -> no deletion (PATCH partial preserved)
  field present, empty list  -> delete all
  field present, list of ids -> upsert listed, delete unlisted
  POST (no instance)         -> no-op

Also verifies:
  - opt-in: only fields listed in `nested_fields_orphan_delete` are affected
  - OneToOneRel targets raise NotImplementedError
"""

import pytest

from apibase.serializers import BaseModelSerializer, NestedOrphanDeleteMixin
from tests.models import Child, OtherChild, Parent, Profile

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Serializer fixtures
# ---------------------------------------------------------------------------


class ChildSerializer(BaseModelSerializer):
    class Meta:
        model = Child
        # `parent` must be in `fields` so apibase's `update_nested` can inject
        # the parent FK into validated_data before save (see L210 / L304-306).
        fields = ["id", "parent", "name", "ordinal"]
        extra_kwargs = {"parent": {"required": False}}


class OtherChildSerializer(BaseModelSerializer):
    class Meta:
        model = OtherChild
        fields = ["id", "parent", "label"]
        extra_kwargs = {"parent": {"required": False}}


class ProfileSerializer(BaseModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "parent", "bio"]
        extra_kwargs = {"parent": {"required": False}}


class ParentSerializer(NestedOrphanDeleteMixin, BaseModelSerializer):
    """Parent serializer: orphan delete is enabled for `child_set` only.

    `otherchild_set` is in nested_fields but NOT in nested_fields_orphan_delete,
    so its children must NEVER be deleted by this mixin (regression guard).
    """

    child_set = ChildSerializer(many=True, required=False)
    otherchild_set = OtherChildSerializer(many=True, required=False)

    nested_fields = ["child_set", "otherchild_set"]
    nested_fields_orphan_delete = ["child_set"]

    class Meta:
        model = Parent
        fields = ["id", "name", "child_set", "otherchild_set"]


class ParentWithProfileSerializer(NestedOrphanDeleteMixin, BaseModelSerializer):
    """For OneToOneRel guard test."""

    profile = ProfileSerializer(required=False)

    nested_fields = ["profile"]
    nested_fields_orphan_delete = ["profile"]

    class Meta:
        model = Parent
        fields = ["id", "name", "profile"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parent_with_children():
    parent = Parent.objects.create(name="p")
    a = Child.objects.create(parent=parent, name="a", ordinal=1)
    b = Child.objects.create(parent=parent, name="b", ordinal=2)
    return parent, a, b


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_post_creates_all_children():
    payload = {
        "name": "new-parent",
        "child_set": [
            {"name": "a", "ordinal": 1},
            {"name": "b", "ordinal": 2},
        ],
    }
    ser = ParentSerializer(data=payload)
    assert ser.is_valid(raise_exception=True)
    parent = ser.save()
    assert parent.child_set.count() == 2
    assert set(parent.child_set.values_list("name", flat=True)) == {"a", "b"}


def test_patch_updates_existing_and_deletes_orphan():
    parent, a, b = _make_parent_with_children()

    payload = {
        "child_set": [{"id": a.id, "name": "a-renamed", "ordinal": 1}],
    }
    ser = ParentSerializer(instance=parent, data=payload, partial=True)
    assert ser.is_valid(raise_exception=True)
    ser.save()

    parent.refresh_from_db()
    remaining = list(parent.child_set.all())
    assert len(remaining) == 1
    assert remaining[0].id == a.id
    assert remaining[0].name == "a-renamed"
    assert not Child.objects.filter(id=b.id).exists()


def test_patch_with_empty_list_deletes_all():
    parent, a, b = _make_parent_with_children()

    payload = {"child_set": []}
    ser = ParentSerializer(instance=parent, data=payload, partial=True)
    assert ser.is_valid(raise_exception=True)
    ser.save()

    parent.refresh_from_db()
    assert parent.child_set.count() == 0
    assert not Child.objects.filter(id__in=[a.id, b.id]).exists()


def test_patch_with_field_absent_keeps_all_children():
    parent, a, b = _make_parent_with_children()

    payload = {"name": "renamed-only"}
    ser = ParentSerializer(instance=parent, data=payload, partial=True)
    assert ser.is_valid(raise_exception=True)
    ser.save()

    parent.refresh_from_db()
    assert parent.name == "renamed-only"
    assert set(parent.child_set.values_list("id", flat=True)) == {a.id, b.id}


def test_patch_with_new_child_no_id_creates_and_deletes_existing():
    parent, a, b = _make_parent_with_children()

    payload = {"child_set": [{"name": "c", "ordinal": 3}]}
    ser = ParentSerializer(instance=parent, data=payload, partial=True)
    assert ser.is_valid(raise_exception=True)
    ser.save()

    parent.refresh_from_db()
    remaining = list(parent.child_set.all())
    assert len(remaining) == 1
    assert remaining[0].name == "c"
    assert not Child.objects.filter(id__in=[a.id, b.id]).exists()


def test_orphan_delete_only_applies_to_listed_fields():
    """`otherchild_set` is in nested_fields but NOT in nested_fields_orphan_delete.

    Even when the payload omits otherchild_set, its existing rows must not be
    deleted. And when an empty list is sent for otherchild_set, the mixin must
    NOT cascade-delete them (because the user did not opt in for that field).
    """
    parent = Parent.objects.create(name="p")
    Child.objects.create(parent=parent, name="kept-child", ordinal=1)
    other_a = OtherChild.objects.create(parent=parent, label="x")
    other_b = OtherChild.objects.create(parent=parent, label="y")

    payload = {"otherchild_set": []}
    ser = ParentSerializer(instance=parent, data=payload, partial=True)
    assert ser.is_valid(raise_exception=True)
    ser.save()

    parent.refresh_from_db()
    surviving_other_ids = set(parent.otherchild_set.values_list("id", flat=True))
    assert surviving_other_ids == {other_a.id, other_b.id}


def test_one_to_one_rel_raises_not_implemented():
    parent = Parent.objects.create(name="p")
    Profile.objects.create(parent=parent, bio="old bio")

    payload = {"profile": {"bio": "new bio"}}
    ser = ParentWithProfileSerializer(instance=parent, data=payload, partial=True)
    assert ser.is_valid(raise_exception=True)

    with pytest.raises(NotImplementedError, match="OneToOneRel"):
        ser.save()
