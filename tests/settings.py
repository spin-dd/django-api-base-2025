"""Django settings module for the test suite.

pytest-django activates only when a settings module is configured (via
``[tool.pytest.ini_options] DJANGO_SETTINGS_MODULE``). Pointing it here lets
pytest-django manage the test database — creating tables for the ``tests`` app
through ``migrate --run-syncdb`` (since ``MIGRATION_MODULES`` disables
migrations for it) — so that ``@pytest.mark.django_db`` works and DB-backed
tests have real tables.

pytest-django sets up Django early (``pytest_load_initial_conftests``), before
any conftest import triggers ``import apibase`` during collection, so the
graphene-django converter auto-registration in ``apibase/__init__.py`` still
runs against configured settings.
"""

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "tests",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# No migrations for the tests app — tables are created directly from model
# definitions via ``migrate --run-syncdb``. Keeps the fixture lightweight and
# avoids shipping throwaway migration files.
MIGRATION_MODULES = {"tests": None}

USE_TZ = True
