"""Tests for the apibase settings singleton and `Settings` class (SET-001..005)."""

import decimal

from django.test import override_settings

import pytest

from apibase.settings import apibase_settings
from apibase.settings.settings import Settings

# ---------------------------------------------------------------------------
# SET-002..005 default values on the configured singleton
# ---------------------------------------------------------------------------


def test_singleton_exposes_documented_defaults():
    assert apibase_settings.URN_NID == "x-nid"
    assert apibase_settings.URN_NSS == "self"
    assert apibase_settings.SCHEME == "https"
    assert apibase_settings.STORAGE_PREFIX == "storage"
    assert apibase_settings.DOMAIN is None
    assert apibase_settings.HOST == "self"


def test_unknown_attribute_raises_attribute_error():
    with pytest.raises(AttributeError):
        _ = apibase_settings.DOES_NOT_EXIST


# ---------------------------------------------------------------------------
# SET-001 override_settings(APIBASE=...) is honoured via a setting_changed reload
# ---------------------------------------------------------------------------


def test_override_settings_updates_singleton_value():
    assert apibase_settings.URN_NID == "x-nid"  # cached default
    with override_settings(APIBASE={"URN_NID": "z-nid"}):
        assert apibase_settings.URN_NID == "z-nid"


def test_override_settings_is_restored_on_exit():
    with override_settings(APIBASE={"URN_NID": "z-nid"}):
        pass
    assert apibase_settings.URN_NID == "x-nid"


# ---------------------------------------------------------------------------
# SET-001 Settings behaviour: override, caching, import strings
# ---------------------------------------------------------------------------


def test_user_settings_override_defaults():
    settings = Settings(user_settings={"URN_NID": "y-nid"}, defaults={"URN_NID": "x-nid"})

    assert settings.URN_NID == "y-nid"


def test_falsy_user_value_falls_back_to_default():
    settings = Settings(user_settings={"SCHEME": ""}, defaults={"SCHEME": "https"})

    assert settings.SCHEME == "https"


def test_attribute_value_is_cached_after_first_access():
    settings = Settings(defaults={"SCHEME": "https"})

    assert "SCHEME" not in settings.__dict__
    _ = settings.SCHEME  # trigger lazy resolution + caching
    assert settings.__dict__["SCHEME"] == "https"


def test_import_string_setting_resolves_to_object():
    settings = Settings(
        user_settings={"ENCODER": "decimal.Decimal"},
        defaults={"ENCODER": None},
        import_strings=["ENCODER"],
    )

    assert settings.ENCODER is decimal.Decimal


def test_dict_default_is_merged_with_user_dict():
    settings = Settings(
        user_settings={"OPTS": {"b": 2}},
        defaults={"OPTS": {"a": 1, "b": 1}},
    )

    assert settings.OPTS == {"a": 1, "b": 2}


# ---------------------------------------------------------------------------
# SET-001 Settings.create wiring
# ---------------------------------------------------------------------------


def test_create_marks_import_string_settings():
    settings = Settings.create(
        "MISSING_SETTING",
        (("PLAIN", (False, "x")), ("IMPORTED", (True, "decimal.Decimal"))),
    )

    assert settings.PLAIN == "x"
    assert settings.IMPORTED is decimal.Decimal
