"""Project-root pytest configuration.

Configures Django at module-import time so that importing :mod:`apibase`
(which auto-registers graphene-django form-field converters and therefore
imports ``graphene_django.settings``) succeeds during the conftest /
collection phase. A late ``pytest_configure`` hook is too late here:
sub-package conftests live inside ``apibase/`` and importing them
triggers the ``apibase`` package init before pytest fires the hook.
"""

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "tests",
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        # No migrations for the tests app — create tables directly from
        # model definitions via `migrate --run-syncdb` semantics. Keeps the
        # test fixture lightweight and avoids shipping migration files for
        # throwaway test models.
        MIGRATION_MODULES={"tests": None},
    )
    django.setup()
