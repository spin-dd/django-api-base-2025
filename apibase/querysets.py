"""QuerySet inspection helpers shared by API transports."""

from django.db.models import ForeignObjectRel, QuerySet
from django.db.models.sql.datastructures import Join


def duplicating_join_aliases(queryset: QuerySet) -> set[str]:
    """Return aliases of JOINs that can repeat a queryset's base row.

    A GenericRelation uses ``GenericRel`` and can report itself as many-to-one,
    so reverse relations are also checked explicitly. The caller decides how
    to handle inspection errors; GraphQL conservatively applies DISTINCT.
    """
    return {
        alias
        for alias, join in queryset.query.alias_map.items()
        if isinstance(join, Join)
        and join.join_field
        and (
            getattr(join.join_field, "many_to_many", False)
            or getattr(join.join_field, "one_to_many", False)
            or (isinstance(join.join_field, ForeignObjectRel) and not join.join_field.one_to_one)
        )
    }
