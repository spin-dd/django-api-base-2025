import graphene
from django import forms
from graphene_django.forms.converter import convert_form_field

from apibase.fields import ListCharField, ListIntegerField


def _is_graphene_list(gtype) -> bool:
    # graphene.List(String) returns an instance of graphene.types.structures.List
    from graphene.types.structures import List as GrapheneList

    return isinstance(gtype, GrapheneList)


def test_apibase_list_fields_are_converted_to_list_via_registered_converter():
    # Demo AppConfig.ready() should have called init_converter() already.
    t_char = convert_form_field(ListCharField(required=False))
    assert _is_graphene_list(t_char)
    assert t_char.of_type is graphene.String

    t_int = convert_form_field(ListIntegerField(required=False))
    assert _is_graphene_list(t_int)
    assert t_int.of_type is graphene.Int


def test_default_converter_list_for_django_multiple_choice():
    # Django's MultipleChoiceField is handled by graphene-django and maps to List(String).
    t = convert_form_field(forms.MultipleChoiceField(required=False))
    assert _is_graphene_list(t)
    assert t.of_type is graphene.String


def test_django_multiple_choice_is_list_by_default():
    t = convert_form_field(forms.MultipleChoiceField(required=False))
    assert _is_graphene_list(t)
    assert t.of_type is graphene.String
