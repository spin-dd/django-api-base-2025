"""Tests for `apibase.fields` form fields (FRM-001..004)."""

from datetime import date

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
    # LATENT BUG (characterized): the non-sequence branch tries to raise
    # ValidationError(self.error_messages["invalid_list"]), but "invalid_list"
    # was never added to error_messages, so it raises KeyError instead of a
    # clean ValidationError. Pinned here until the message key is added.
    with pytest.raises(KeyError):
        ListCharField().to_python("not-a-list")


# ---------------------------------------------------------------------------
# FRM-002 ListIntegerField
# ---------------------------------------------------------------------------


def test_list_integer_field_coerces_each_item_to_int():
    assert ListIntegerField().to_python(["1", "2", 3]) == [1, 2, 3]


def test_list_integer_field_empty_input_returns_empty_list():
    assert ListIntegerField().to_python([]) == []


def test_list_integer_field_rejects_non_sequence():
    # Same latent bug as ListCharField (see note above): raises KeyError
    # rather than a clean ValidationError for non-sequence input.
    with pytest.raises(KeyError):
        ListIntegerField().to_python("12")


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
