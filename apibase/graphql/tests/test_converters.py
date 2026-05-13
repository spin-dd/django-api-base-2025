"""Tests for auto-registered graphene-django form-field converters.

The registrations live in :mod:`apibase.graphql.converters` and run as a
side effect of ``import apibase``. These tests assert that each apibase
form field class converts to the correct graphene type, which is the
primary contract relied on by all ``__in`` / ``__nin`` GraphQL filters in
downstream projects.
"""

import subprocess
import sys

import graphene
from django_filters.fields import MultipleChoiceField
from graphene_django.forms.converter import convert_form_field

# Importing apibase triggers converter registration.
import apibase  # noqa: F401
from apibase.fields import ListCharField, ListIntegerField, MonthRangeField


def _unwrap(node):
    """Drill into a ``graphene.List`` / ``NonNull`` wrapper one level."""
    return getattr(node, "_of_type", None) or getattr(node, "of_type", None)


def _assert_list_of_non_null(converted, inner_scalar):
    """Assert ``converted`` represents ``[inner_scalar!]`` in the GraphQL SDL."""
    assert isinstance(converted, graphene.List), f"expected graphene.List, got {converted!r}"
    item = _unwrap(converted)
    assert isinstance(item, graphene.NonNull), (
        f"list items must be NonNull-wrapped (i.e. [{inner_scalar.__name__}!]), got {item!r}"
    )
    assert _unwrap(item) is inner_scalar, f"NonNull inner type must be {inner_scalar.__name__}, got {_unwrap(item)!r}"


def test_list_char_field_converts_to_list_non_null_string():
    field = ListCharField(required=False)
    _assert_list_of_non_null(convert_form_field(field), graphene.String)


def test_list_integer_field_converts_to_list_non_null_int():
    field = ListIntegerField(required=False)
    _assert_list_of_non_null(convert_form_field(field), graphene.Int)


def test_month_range_field_converts_to_string():
    field = MonthRangeField(required=False)
    converted = convert_form_field(field)
    assert isinstance(converted, graphene.String)


def test_multiple_choice_field_converts_to_list_non_null_string():
    field = MultipleChoiceField(choices=[("a", "A")], required=False)
    _assert_list_of_non_null(convert_form_field(field), graphene.String)


def test_importing_apibase_without_configured_django_does_not_raise():
    """``import apibase`` must remain safe before Django is configured.

    The converter registration is intentionally guarded by a try/except so
    that REST-only consumers, packaging scripts, and CLI tools can import
    the package without first calling ``django.setup()``. Run in a child
    process to guarantee a pristine settings state.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import apibase; print(apibase.__version__)"],
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": __import__("os").environ.get("PATH", "")},
    )
    assert result.returncode == 0, (
        f"`import apibase` failed without Django settings configured:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert apibase.__version__ in result.stdout
