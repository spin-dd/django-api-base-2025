import re
from urllib.parse import quote, unquote

import graphene
import six
from django_filters.fields import MultipleChoiceField
from django_filters.filters import RangeFilter
from django_filters.utils import get_model_field
from gql import Client, gql
from graphene_django.forms.converter import convert_form_field
from graphene_django.settings import graphene_settings
from graphql_relay import to_global_id
from graphql_relay import get_offset_with_default

from .fields import ListCharField, ListIntegerField, MonthRangeField


def get_filtering_args_from_filterset(filterset_class, type, obvious_filters=None):
    """
    Original:
        - https://github.com/graphql-python/graphene-django/blob/master/graphene_django/filter/utils.py#L7
        - filters not in 'declared_filters' are defined by Graphene-Django for model fields `formfield`.

    obivius_filters:
        - Force to use field class defined in filters.
    """

    args = {}
    obvious_filters = obvious_filters or []
    model = filterset_class._meta.model
    for name, filter_field in six.iteritems(filterset_class.base_filters):
        form_field = None

        if name in filterset_class.declared_filters:
            form_field = filter_field.field
        elif filter_field.__class__ in obvious_filters:
            form_field = filter_field.field
        else:
            model_field = get_model_field(model, filter_field.field_name)
            filter_type = filter_field.lookup_expr
            if filter_type != "isnull" and hasattr(model_field, "formfield"):
                form_field = model_field.formfield(
                    required=filter_field.extra.get("required", False)
                )

        # Fallback to field defined on filter if we can't get it from the
        # model field
        if not form_field:
            form_field = filter_field.field

        field_type = convert_form_field(form_field).Argument()
        field_type.description = filter_field.label

        # For RangeFilter, duplicate filter args for suffixes
        if isinstance(filter_field, RangeFilter) and hasattr(
            filter_field.field, "widget"
        ):
            suffixes = getattr(filter_field.field.widget, "suffixes", [])
            for s in suffixes:
                if s:
                    args[f"{name}_{s}"] = field_type
        else:
            args[name] = field_type

    return args


def resolve_start_offset(slice_start, after):
    after_offset = get_offset_with_default(after, -1)
    return max(slice_start - 1, after_offset, -1) + 1


def gql_query(schema, query_str, **params):
    client = Client(schema=schema)
    query = gql(query_str)
    return client.execute(query, variable_values=params)


def to_gql_relay_id(schema_name, id):
    return to_global_id(schema_name, id)


def to_content_disposition(filename):
    utf8_filename = quote(filename)
    return f"attachment; filename*=utf-8''{utf8_filename}"


def query_instance(
    query_string, instance=None, object_name=None, id=None, schema=None, **kwargs
):
    schema = schema or graphene_settings.SCHEMA
    if instance:
        object_name = instance._meta.object_name
        id = instance.id

    if object_name and id:
        id = to_gql_relay_id(object_name, id)

    return gql_query(schema, query_string, id=id, **kwargs)


def query(query_string, schema=None, **params):
    schema = schema or graphene_settings.SCHEMA
    if "instance" in params or ("object_name" in params and "id" in params):
        return query_instance(query_string, **params)

    return gql_query(schema, query_string, **params)


def init_converter():
    convert_form_field.register(
        MultipleChoiceField,
        lambda field: graphene.List(graphene.String, required=field.required),
    )

    convert_form_field.register(
        ListCharField,
        lambda field: graphene.List(graphene.String, required=field.required),
    )

    convert_form_field.register(
        ListIntegerField,
        lambda field: graphene.List(graphene.Int, required=field.required),
    )

    convert_form_field.register(
        MonthRangeField,
        lambda field: graphene.String(required=field.required),
    )


def get_filename_from_header(header):
    """rfc6266: https://datatracker.ietf.org/doc/html/rfc6266"""
    source = header.get("Content-Disposition", None)
    if not source:
        return

    ma = re.search(r"filename.+utf.*8''([^;]+)", source)
    if ma:
        return unquote(ma.groups()[0])
