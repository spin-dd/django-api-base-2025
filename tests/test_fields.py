"""Tests for `apibase.fields` form fields (FRM-001..004)."""

from datetime import date

from django.core.exceptions import ValidationError

import pytest

from apibase.fields import CharRangeWidget, ListCharField, ListIntegerField, MonthRangeField

# ---------------------------------------------------------------------------
# FRM-001 ListCharField
# ---------------------------------------------------------------------------


def test_list_char_field_coerces_each_item_to_str():
    assert ListCharField().to_python([1, "a", 2]) == ["1", "a", "2"]


def test_list_char_field_empty_input_returns_empty_list():
    assert ListCharField().to_python([]) == []
    assert ListCharField().to_python(None) == []


def test_list_char_field_rejects_non_sequence():
    # Non-sequence input is rejected with a clean ValidationError carrying the
    # "invalid_list" message (defined via ListFieldMixin.default_error_messages),
    # rather than leaking a KeyError on a missing message key.
    with pytest.raises(ValidationError):
        ListCharField().to_python("not-a-list")


@pytest.mark.parametrize("value", [0, False], ids=["zero", "false"])
def test_list_char_field_rejects_falsy_scalar(value):
    # A falsy scalar like 0/False is NOT an empty value; only explicit-empty
    # values (None, '', [], (), {}) map to []. Everything else non-list/tuple raises.
    with pytest.raises(ValidationError):
        ListCharField().to_python(value)


def test_list_char_field_drops_empty_members():
    # `?key=` reaches the form as [""] (QueryDict.getlist). Treating it as a value
    # would filter on the empty string; "nothing selected" must mean "no filter".
    assert ListCharField().to_python([""]) == []
    assert ListCharField().to_python([None]) == []
    assert ListCharField().to_python(["a", "", "b"]) == ["a", "b"]


# ---------------------------------------------------------------------------
# FRM-002 ListIntegerField
# ---------------------------------------------------------------------------


def test_list_integer_field_coerces_each_item_to_int():
    assert ListIntegerField().to_python(["1", "2", 3]) == [1, 2, 3]


def test_list_integer_field_empty_input_returns_empty_list():
    assert ListIntegerField().to_python([]) == []


def test_list_integer_field_rejects_non_sequence():
    # Like ListCharField, non-sequence input yields a clean ValidationError
    # (the "invalid_list" message) instead of a KeyError.
    with pytest.raises(ValidationError):
        ListIntegerField().to_python("12")


def test_list_integer_field_wraps_converter_failure_as_validation_error():
    # A list item that cannot be converted (int("x") raises ValueError) must be
    # surfaced as a clean ValidationError, not a leaked ValueError.
    with pytest.raises(ValidationError):
        ListIntegerField().to_python(["x"])


def test_list_integer_field_drops_empty_members():
    # Same rule as ListCharField. Without this, `?key=` raises ValidationError
    # (int("") -> ValueError) and the request 400s instead of skipping the filter.
    assert ListIntegerField().to_python([""]) == []
    assert ListIntegerField().to_python(["1", "", "2"]) == [1, 2]


def test_list_integer_field_keeps_zero():
    # 0 is a real value, not an empty one -- it must survive the empty-member drop.
    assert ListIntegerField().to_python(["0", 0]) == [0, 0]


# ---------------------------------------------------------------------------
# FRM-003 CharRangeWidget
# ---------------------------------------------------------------------------


def test_char_range_widget_uses_after_before_suffixes():
    widget = CharRangeWidget()
    data = {"period_after": "a", "period_before": "z"}

    assert widget.value_from_datadict(data, {}, "period") == ["a", "z"]


def test_char_range_widget_unwraps_list_values():
    widget = CharRangeWidget()
    # SuffixedMultiWidget may yield list-wrapped values; they are flattened.
    data = {"period_after": ["a"], "period_before": ["z"]}

    assert widget.value_from_datadict(data, {}, "period") == ["a", "z"]


# ---------------------------------------------------------------------------
# FRM-004 MonthRangeField
# ---------------------------------------------------------------------------


def test_month_range_field_compresses_to_month_slice():
    result = MonthRangeField().compress(["202401", "202403"])

    assert result == slice(date(2024, 1, 1), date(2024, 3, 31))


def test_month_range_field_uses_last_day_of_end_month():
    # February of a leap year ends on the 29th.
    result = MonthRangeField().compress(["202402", "202402"])

    assert result.stop == date(2024, 2, 29)


def test_month_range_field_empty_input_returns_none():
    assert MonthRangeField().compress([]) is None
