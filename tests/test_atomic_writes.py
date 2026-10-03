"""A failed nested write must leave no partial database changes."""

from django.db import IntegrityError
from django.dispatch import Signal
from django.test import TransactionTestCase, override_settings

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apibase.serializers import BaseModelSerializer, BatchListSerializer, BatchSerializerMixin
from apibase.viewsets import BaseModelViewSet
from tests.models import Child, Parent


class ChildSerializer(BaseModelSerializer):
    # Let NULL reach the real NOT NULL constraint to exercise database failures.
    name = serializers.CharField(allow_null=True)

    class Meta:
        model = Child
        fields = ["id", "parent", "name"]


class ParentSerializer(BaseModelSerializer):
    child_set = ChildSerializer(many=True, required=False)
    nested_fields = ["child_set"]

    class Meta:
        model = Parent
        fields = ["id", "name", "child_set"]


class TestNestedCreate(TransactionTestCase):
    def test_child_validation_error_rolls_back_parent_and_earlier_child(self):
        serializer = ParentSerializer(
            data={"name": "new parent", "child_set": [{"name": "first child"}, {"name": ""}]}
        )
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(ValidationError):
            serializer.save()

        self.assertEqual(list(Parent.objects.values_list("name", flat=True)), [])
        self.assertEqual(list(Child.objects.values_list("name", flat=True)), [])

    def test_child_database_error_rolls_back_parent_and_earlier_child(self):
        serializer = ParentSerializer(
            data={"name": "new parent", "child_set": [{"name": "first child"}, {"name": None}]}
        )
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(IntegrityError):
            serializer.save()

        self.assertEqual(list(Parent.objects.values_list("name", flat=True)), [])
        self.assertEqual(list(Child.objects.values_list("name", flat=True)), [])

    def test_success_saves_parent_and_all_children(self):
        serializer = ParentSerializer(
            data={"name": "new parent", "child_set": [{"name": "first child"}, {"name": "second child"}]}
        )
        serializer.is_valid(raise_exception=True)
        parent = serializer.save()

        parent.refresh_from_db()
        self.assertEqual(parent.name, "new parent")
        self.assertEqual(
            list(parent.child_set.order_by("id").values_list("name", flat=True)), ["first child", "second child"]
        )


@override_settings(DATABASE_ROUTERS=["tests.routers.NestedWriteRouter"])
class TestRoutedNestedCreate(TestNestedCreate):
    databases = {"default", "nested"}

    def test_success_saves_parent_and_all_children(self):
        super().test_success_saves_parent_and_all_children()
        self.assertEqual(Parent.objects.using("nested").count(), 1)
        self.assertEqual(Child.objects.using("nested").count(), 2)
        self.assertEqual(Parent.objects.using("default").count(), 0)
        self.assertEqual(Child.objects.using("default").count(), 0)


class TestNestedUpdate(TransactionTestCase):
    def setUp(self):
        self.parent = Parent.objects.create(name="original parent")
        self.child = Child.objects.create(parent=self.parent, name="original child")

    def test_child_validation_error_restores_parent_and_earlier_children(self):
        serializer = ParentSerializer(
            self.parent,
            data={
                "name": "changed parent",
                "child_set": [
                    {"id": self.child.id, "name": "changed child"},
                    {"name": "new child"},
                    {"name": ""},
                ],
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(ValidationError):
            serializer.save()

        self.parent.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(self.parent.name, "original parent")
        self.assertEqual(self.child.name, "original child")
        self.assertEqual(list(self.parent.child_set.values_list("id", flat=True)), [self.child.id])

    def test_child_database_error_restores_parent_and_earlier_children(self):
        serializer = ParentSerializer(
            self.parent,
            data={
                "name": "changed parent",
                "child_set": [
                    {"id": self.child.id, "name": "changed child"},
                    {"name": "new child"},
                    {"name": None},
                ],
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        with self.assertRaises(IntegrityError):
            serializer.save()

        self.parent.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(self.parent.name, "original parent")
        self.assertEqual(self.child.name, "original child")
        self.assertEqual(list(self.parent.child_set.values_list("id", flat=True)), [self.child.id])

    def test_success_updates_parent_and_children(self):
        serializer = ParentSerializer(
            self.parent,
            data={
                "name": "changed parent",
                "child_set": [
                    {"id": self.child.id, "name": "changed child"},
                    {"name": "new child"},
                ],
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.parent.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(self.parent.name, "changed parent")
        self.assertEqual(self.child.name, "changed child")
        self.assertEqual(
            list(self.parent.child_set.order_by("id").values_list("name", flat=True)), ["changed child", "new child"]
        )


@override_settings(DATABASE_ROUTERS=["tests.routers.InstanceHintWriteRouter"])
class TestRoutedNestedUpdate(TestNestedUpdate):
    databases = {"default", "nested"}

    def setUp(self):
        self.parent = Parent.objects.using("nested").create(name="original parent")
        self.child = Child.objects.using("nested").create(parent=self.parent, name="original child")


class PlainParentSerializer(BaseModelSerializer):
    name = serializers.CharField(allow_null=True)

    class Meta:
        model = Parent
        fields = ["id", "name"]


class BatchParentSerializer(BatchSerializerMixin, PlainParentSerializer):
    class Meta(PlainParentSerializer.Meta):
        list_serializer_class = BatchListSerializer


class ParentViewSet(BaseModelViewSet):
    queryset = Parent.objects.order_by("id")
    # Creation must also work with DRF's default ListSerializer.
    serializer_class = PlainParentSerializer


class BatchParentViewSet(ParentViewSet):
    serializer_class = BatchParentSerializer


class ParentAwareChildSerializer(ChildSerializer):
    def validate(self, attrs):
        if attrs["name"] == attrs["parent"].name:
            raise ValidationError("A child name must differ from its parent name.")
        return attrs


class NestedBatchParentSerializer(BatchSerializerMixin, ParentSerializer):
    child_set = ParentAwareChildSerializer(many=True, required=False)
    nested_fields_updateds_signal = Signal()

    class Meta(ParentSerializer.Meta):
        list_serializer_class = BatchListSerializer


class NestedBatchParentViewSet(ParentViewSet):
    serializer_class = NestedBatchParentSerializer


class TestBatchCreate(TransactionTestCase):
    def test_child_validation_error_in_second_record_rolls_back_all_records(self):
        completed = []

        def record_saved_parent(sender, instance, **kwargs):
            completed.append((instance.name, list(instance.child_set.values_list("name", flat=True))))

        signal = NestedBatchParentSerializer.nested_fields_updateds_signal
        signal.connect(record_saved_parent)
        try:
            request = APIRequestFactory().post(
                "/parents/batch_create/",
                [
                    {"name": "first", "child_set": [{"name": "second"}]},
                    {"name": "second", "child_set": [{"name": "second"}]},
                ],
                format="json",
            )
            response = NestedBatchParentViewSet.as_view({"post": "batch_create"})(request)
        finally:
            signal.disconnect(record_saved_parent)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(completed, [("first", ["second"])])
        self.assertEqual(list(Parent.objects.values_list("name", flat=True)), [])
        self.assertEqual(list(Child.objects.values_list("name", flat=True)), [])

    def test_database_error_in_second_record_rolls_back_first_record(self):
        request = APIRequestFactory().post(
            "/parents/batch_create/", [{"name": "first"}, {"name": None}], format="json"
        )

        with self.assertRaises(IntegrityError):
            ParentViewSet.as_view({"post": "batch_create"})(request)

        self.assertEqual(list(Parent.objects.values_list("name", flat=True)), [])

    def test_success_saves_all_records(self):
        request = APIRequestFactory().post(
            "/parents/batch_create/", [{"name": "first"}, {"name": "second"}], format="json"
        )
        response = ParentViewSet.as_view({"post": "batch_create"})(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(list(Parent.objects.order_by("id").values_list("name", flat=True)), ["first", "second"])


@override_settings(DATABASE_ROUTERS=["tests.routers.NestedWriteRouter"])
class TestRoutedBatchCreate(TestBatchCreate):
    databases = {"default", "nested"}


class TestBatchUpdate(TransactionTestCase):
    def test_child_validation_error_in_second_record_restores_all_records(self):
        first = Parent.objects.create(name="original first")
        second = Parent.objects.create(name="original second")
        first_child = Child.objects.create(parent=first, name="original first child")
        second_child = Child.objects.create(parent=second, name="original second child")
        completed = []

        def record_saved_parent(sender, instance, **kwargs):
            completed.append((instance.name, list(instance.child_set.values_list("name", flat=True))))

        signal = NestedBatchParentSerializer.nested_fields_updateds_signal
        signal.connect(record_saved_parent)
        try:
            request = APIRequestFactory().patch(
                "/parents/batch_update/",
                [
                    {"id": first.id, "name": "changed first", "child_set": [{"name": "changed second"}]},
                    {"id": second.id, "name": "changed second", "child_set": [{"name": "changed second"}]},
                ],
                format="json",
            )
            response = NestedBatchParentViewSet.as_view({"patch": "batch_update"})(request)
        finally:
            signal.disconnect(record_saved_parent)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(completed, [("changed first", ["original first child", "changed second"])])
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.name, "original first")
        self.assertEqual(second.name, "original second")
        self.assertEqual(list(first.child_set.values_list("id", flat=True)), [first_child.id])
        self.assertEqual(list(second.child_set.values_list("id", flat=True)), [second_child.id])

    def test_database_error_in_second_record_restores_first_record(self):
        first = Parent.objects.create(name="original first")
        second = Parent.objects.create(name="original second")
        request = APIRequestFactory().patch(
            "/parents/batch_update/",
            [{"id": first.id, "name": "changed first"}, {"id": second.id, "name": None}],
            format="json",
        )

        with self.assertRaises(IntegrityError):
            BatchParentViewSet.as_view({"patch": "batch_update"})(request)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.name, "original first")
        self.assertEqual(second.name, "original second")

    def test_success_updates_all_records(self):
        first = Parent.objects.create(name="original first")
        second = Parent.objects.create(name="original second")
        request = APIRequestFactory().patch(
            "/parents/batch_update/",
            [{"id": first.id, "name": "changed first"}, {"id": second.id, "name": "changed second"}],
            format="json",
        )
        response = BatchParentViewSet.as_view({"patch": "batch_update"})(request)

        self.assertEqual(response.status_code, 200)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.name, "changed first")
        self.assertEqual(second.name, "changed second")


@override_settings(DATABASE_ROUTERS=["tests.routers.NestedWriteRouter"])
class TestRoutedBatchUpdate(TestBatchUpdate):
    databases = {"default", "nested"}
