import django_filters

from apibase.filters import BaseFilter, ListCharInFilter

from .models import Book


class BookFilter(BaseFilter):
    # Custom list-in (char) using apibase filter
    author__in_list = ListCharInFilter(label="author in list", field_name="author")

    # MultipleChoiceFilter example (static choices for demo)
    author__in_multi = django_filters.MultipleChoiceFilter(
        field_name="author", choices=[("Dev", "Dev"), ("Anon", "Anon"), ("Other", "Other")]
    )

    class Meta:
        model = Book
        fields = {
            "id": ["exact", "in"],
            "title": ["exact", "icontains"],
            "author": ["exact", "icontains"],
            "published": ["exact", "lte", "gte"],
        }
