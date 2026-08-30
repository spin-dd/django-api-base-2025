"""Auto-register graphene-django form-field converters for apibase fields.

Importing this module has a side effect: it registers handlers on
``graphene_django.forms.converter.convert_form_field`` so that filters
declared with :class:`apibase.fields.ListCharField`,
:class:`apibase.fields.ListIntegerField`,
:class:`apibase.fields.MonthRangeField`, and
``django_filters.fields.MultipleChoiceField`` get exposed as the correct
GraphQL list / scalar types instead of falling back to ``String``.

Without these registrations, list-style filters such as
``employee_kind__in = ListCharInFilter(...)`` are surfaced in the GraphQL
schema as ``String`` (the default for the underlying ``forms.CharField``
parent class), which makes them unusable from any GraphQL client because
the schema rejects list literals at type-validation time.
"""

import graphene
from django_filters.fields import MultipleChoiceField
from graphene_django.forms.converter import convert_form_field

from apibase.fields import ListCharField, ListIntegerField, MonthRangeField


@convert_form_field.register(MultipleChoiceField)
def _convert_multiple_choice(field):
    return graphene.List(graphene.NonNull(graphene.String), required=field.required)


@convert_form_field.register(ListCharField)
def _convert_list_char(field):
    return graphene.List(graphene.NonNull(graphene.String), required=field.required)


@convert_form_field.register(ListIntegerField)
def _convert_list_integer(field):
    return graphene.List(graphene.NonNull(graphene.Int), required=field.required)


@convert_form_field.register(MonthRangeField)
def _convert_month_range(field):
    return graphene.String(required=field.required)
