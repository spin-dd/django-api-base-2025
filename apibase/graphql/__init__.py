"""apibase GraphQL integration.

Importing this package registers graphene-django form-field converters
for apibase's custom form fields. See :mod:`apibase.graphql.converters`.
"""

from . import converters  # noqa: F401  (registers converters on import)
