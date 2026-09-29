from django.db import models


class Parent(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"


class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    ordinal = models.IntegerField(default=0)

    class Meta:
        app_label = "tests"
        ordering = ["ordinal", "id"]


class OtherChild(models.Model):
    """Second nested relation on Parent. Used to verify opt-in semantics:
    a serializer can declare Child in nested_fields_orphan_delete while
    leaving OtherChild untouched, even though both are in nested_fields.
    """

    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    label = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"


class Profile(models.Model):
    """OneToOne reverse relation on Parent — used to verify NotImplementedError."""

    parent = models.OneToOneField(Parent, on_delete=models.CASCADE)
    bio = models.CharField(max_length=200)

    class Meta:
        app_label = "tests"


class BatchItem(models.Model):
    """Two required writable fields — used to verify batch PATCH stays partial."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class Vendor(models.Model):
    """Default manager narrows; a second manager does not.

    Used to verify that fan-out folding evaluates its subquery against the
    unfiltered base manager: a ViewSet may legitimately hand the FilterSet a
    queryset broader than the default manager.
    """

    name = models.CharField(max_length=100)
    deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        app_label = "tests"


class VendorTag(models.Model):
    """Reverse FK on Vendor — the multi-value relation the fan-out filter folds."""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "tests"
