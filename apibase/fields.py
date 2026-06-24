import calendar
from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import SelectMultiple
from django.utils.translation import gettext_lazy as _

from django_filters.fields import RangeField
from django_filters.widgets import SuffixedMultiWidget


class ListFieldMixin:
    converter = str
    default_error_messages = {"invalid_list": _("Enter a list of values.")}

    def to_python_value(self, value):
        if value in self.empty_values:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["invalid_list"], code="invalid_list")
        try:
            return [self.converter(val) for val in value]
        except (TypeError, ValueError):
            raise ValidationError(self.error_messages["invalid_list"], code="invalid_list")


class ListCharField(forms.CharField, ListFieldMixin):
    widget = SelectMultiple

    def to_python(self, value):
        return self.to_python_value(value)


class ListIntegerField(forms.IntegerField, ListFieldMixin):
    widget = SelectMultiple
    converter = int

    def to_python(self, value):
        return self.to_python_value(value)


class CharRangeField(RangeField):
    def __init__(self, fields=None, *args, **kwargs):
        if fields is None:
            fields = (forms.CharField(), forms.CharField())
        super().__init__(fields, *args, **kwargs)


class CharRangeWidget(SuffixedMultiWidget):
    suffixes = ["after", "before"]

    def __init__(self, attrs=None):
        widgets = (forms.TextInput, forms.TextInput)
        super().__init__(widgets, attrs)

    def value_from_datadict(self, data, files, name):
        res = super().value_from_datadict(data, files, name)
        return [isinstance(i, list) and i[0] or i for i in res]


class MonthRangeField(CharRangeField):
    widget = CharRangeWidget

    def to_date(self, value, last=False):
        if value:
            ret = date(int(str(value)[:4]), int(str(value)[4:]), 1)
            if last:
                _, day = calendar.monthrange(ret.year, ret.month)
                return ret.replace(day=day)
            return ret

    def compress(self, data_list):
        data = data_list and [
            self.to_date(data_list[0]),
            self.to_date(data_list[1], last=True),
        ]
        if data:
            return slice(*data)
        return None
