__version__ = "0.4.0"

# Eagerly trigger GraphQL form-field converter registration so that filters
# using ListCharField / ListIntegerField surface the correct GraphQL types
# (``[String!]`` / ``[Int!]``) instead of falling back to ``String``.
#
# Only attempt the import when Django settings have been configured.
# ``apibase.graphql.converters`` imports ``graphene_django``, which reads
# Django settings at its own import time. REST-only consumers, packaging
# scripts, and CLI tools that touch ``apibase`` before ``django.setup()``
# would otherwise crash; in that case registration is deferred and runs
# when something explicitly imports ``apibase.graphql`` later (e.g., during
# URL / schema resolution after Django has been set up). Using
# ``settings.configured`` here -- rather than ``try / except
# ImproperlyConfigured`` -- avoids silently swallowing real misconfiguration
# such as an invalid ``DJANGO_SETTINGS_MODULE``.
from django.conf import settings  # noqa: E402

if settings.configured:
    from . import graphql  # noqa: F401, E402
