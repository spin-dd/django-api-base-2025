"""Tests for `apibase.urn` (URN-001, URN-002, URN-003).

URN-002 had a confirmed latent bug: prefix validation was a no-op because the
unpacked first token shadowed the `prefix` parameter and the guard compared a
name to itself (`prefix == prefix`). The bug is fixed; the regression tests
below pin the corrected behaviour (wrong prefix -> None, explicit `prefix`
honoured) while the round-trip tests guard against breaking valid URNs.
"""

from django.test import override_settings

from apibase.urn import model_urn, parse_urn, rest_endpoint_from_urn
from tests.models import Parent

# ---------------------------------------------------------------------------
# URN-001 model_urn
# ---------------------------------------------------------------------------


def test_model_urn_uses_apibase_defaults():
    assert model_urn(Parent(id=7)) == "urn:x-nid:self:tests:parent:7"


def test_model_urn_honours_nss_and_nid_overrides():
    assert model_urn(Parent(id=7), nss="acme", nid="y-nid") == "urn:y-nid:acme:tests:parent:7"


def test_model_urn_returns_empty_string_without_meta():
    assert model_urn(object()) == ""


# ---------------------------------------------------------------------------
# URN-002 parse_urn
# ---------------------------------------------------------------------------


def test_parse_urn_parses_valid_urn_into_components():
    result = parse_urn("urn:x-nid:self:tests:parent:7")

    assert result == {
        "nid": "x-nid",
        "nss": "self",
        "app_label": "tests",
        "model_name": "parent",
        "others": ["7"],
    }


def test_parse_urn_collects_trailing_segments_into_others():
    result = parse_urn("urn:x-nid:self:tests:parent:7:extra")

    assert result["others"] == ["7", "extra"]


def test_parse_urn_returns_none_on_nid_mismatch():
    assert parse_urn("urn:other-nid:self:tests:parent:7") is None


def test_parse_urn_round_trips_with_model_urn():
    parsed = parse_urn(model_urn(Parent(id=42)))

    assert parsed["app_label"] == "tests"
    assert parsed["model_name"] == "parent"
    assert parsed["others"] == ["42"]


def test_parse_urn_rejects_wrong_prefix():
    # Regression for the prefix-shadow bug: a string that does not start with
    # the expected "urn" prefix must not parse.
    assert parse_urn("xxx:x-nid:self:tests:parent:7") is None


def test_parse_urn_honours_explicit_prefix_argument():
    # The `prefix` parameter is actually validated now.
    assert parse_urn("urn:x-nid:self:tests:parent:7", prefix="other") is None
    assert parse_urn("ark:x-nid:self:tests:parent:7", prefix="ark") is not None


# ---------------------------------------------------------------------------
# URN-003 rest_endpoint_from_urn
# ---------------------------------------------------------------------------


def test_rest_endpoint_from_urn_builds_url_with_explicit_domain():
    url = rest_endpoint_from_urn("urn:x-nid:self:tests:parent:7", domain="example.com")

    assert url == "https://example.com/api/rest/tests/parent/7/"


def test_rest_endpoint_from_urn_omits_service_for_self_nss():
    url = rest_endpoint_from_urn("urn:x-nid:self:tests:parent:7", domain="example.com")

    assert "://example.com" in url  # no leading service subdomain


def test_rest_endpoint_from_urn_prepends_service_for_non_self_nss():
    url = rest_endpoint_from_urn("urn:x-nid:acme:tests:parent:7", domain="example.com")

    assert url == "https://acme.example.com/api/rest/tests/parent/7/"


def test_rest_endpoint_from_urn_returns_none_on_parse_failure():
    assert rest_endpoint_from_urn("not-a-urn", domain="example.com") is None


def test_rest_endpoint_from_urn_prefers_domain_setting_over_current_site():
    with override_settings(APIBASE={"DOMAIN": "configured.example"}):
        url = rest_endpoint_from_urn("urn:x-nid:self:tests:parent:7")

    assert url == "https://configured.example/api/rest/tests/parent/7/"
