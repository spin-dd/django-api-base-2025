from django.core.signals import setting_changed
from django.dispatch import receiver

from .settings import Settings

apibase_settings = Settings.create(
    "APIBASE",
    (
        ("URN_NID", (False, "x-nid")),
        ("URN_NSS", (False, "self")),
        ("HOST", (False, "self")),
        ("DOMAIN", (False, None)),
        ("SCHEME", (False, "https")),
        ("STORAGE_PREFIX", (False, "storage")),
    ),
)


@receiver(setting_changed)
def reload_apibase_settings(*, setting, **kwargs):
    """Reload ``apibase_settings`` when the APIBASE setting is overridden.

    Enables ``@override_settings(APIBASE={...})`` in tests and dynamic settings
    changes at runtime by invalidating the singleton's cached attributes.
    """
    if setting == "APIBASE":
        apibase_settings.reload()
