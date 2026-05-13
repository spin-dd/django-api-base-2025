__version__ = "0.3.0"

# Eagerly trigger GraphQL form-field converter registration so that filters
# using ListCharField / ListIntegerField surface the correct GraphQL types
# (``[String!]`` / ``[Int!]``) instead of falling back to ``String``.
#
# Registration is guarded because ``apibase.graphql.converters`` imports
# ``graphene_django``, which reads Django settings at its own import time.
# REST-only consumers, packaging scripts, and CLI tools that import
# ``apibase`` before Django is configured must not crash; in those cases the
# import is deferred and will run later when something explicitly imports
# ``apibase.graphql`` (e.g., during URL / schema resolution after Django
# setup has completed).
from django.core.exceptions import ImproperlyConfigured  # noqa: E402

try:
    from . import graphql  # noqa: F401, E402
except ImproperlyConfigured:
    pass
