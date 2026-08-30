"""Project-root pytest configuration.

Django setup and test-database management are handled by pytest-django, wired
via ``[tool.pytest.ini_options] DJANGO_SETTINGS_MODULE = "tests.settings"`` in
``pyproject.toml`` — see ``tests/settings.py`` for the rationale. The fallback
below only fires if the suite is run without that wiring, and defers to the same
settings module rather than re-declaring configuration.
"""

import os

import django
from django.conf import settings

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    django.setup()
