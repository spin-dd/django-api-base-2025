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
