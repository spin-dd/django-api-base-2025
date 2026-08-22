from importlib.metadata import PackageNotFoundError, version as _dist_version

try:
    # 出所は pyproject.toml の 1 箇所だけにする。ここに文字列を写すと release の
    # たびに手で揃える必要があり、実際 pyproject が 0.4.5 になっても
    # ここは 0.4.0 のまま取り残されていた。
    __version__ = _dist_version("apibase")
except PackageNotFoundError:
    # インストールされていない source tree から import されたとき。嘘の版を
    # 名乗るより「不明」と分かる値を返す。
    __version__ = "0.0.0"

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
