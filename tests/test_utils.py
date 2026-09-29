"""Tests for pure helpers in `apibase.utils` and `apibase.graphql.utils`.

Covers GQU-006 to_content_disposition, GQU-007 get_filename_from_header
(round-trip), and GQU-001 strip_relay.
"""

from apibase.graphql.utils import strip_relay
from apibase.utils import get_filename_from_header, to_content_disposition

# ---------------------------------------------------------------------------
# GQU-006 / GQU-007 Content-Disposition round-trip
# ---------------------------------------------------------------------------


def test_to_content_disposition_uses_rfc6266_utf8_form():
    header = to_content_disposition("report.csv")

    assert header == "attachment; filename*=utf-8''report.csv"


def test_content_disposition_round_trips_ascii_filename():
    header = to_content_disposition("report.csv")

    assert get_filename_from_header({"Content-Disposition": header}) == "report.csv"


def test_content_disposition_round_trips_utf8_filename():
    filename = "請求書 2024.pdf"
    header = to_content_disposition(filename)

    assert get_filename_from_header({"Content-Disposition": header}) == filename


def test_get_filename_from_header_returns_none_when_missing():
    assert get_filename_from_header({}) is None


def test_get_filename_from_header_returns_none_for_non_utf8_disposition():
    assert get_filename_from_header({"Content-Disposition": "attachment; filename=plain.txt"}) is None


# ---------------------------------------------------------------------------
# GQU-001 strip_relay
# ---------------------------------------------------------------------------


def test_strip_relay_flattens_edges_into_node_list():
    data = {"edges": [{"node": {"id": 1}}, {"node": {"id": 2}}]}

    assert strip_relay(data) == [{"id": 1}, {"id": 2}]


def test_strip_relay_non_recursive_leaves_nested_connections():
    data = {"edges": [{"node": {"children": {"edges": [{"node": {"id": 9}}]}}}]}

    result = strip_relay(data)

    # Without recursion the inner connection is left untouched.
    assert result == [{"children": {"edges": [{"node": {"id": 9}}]}}]


def test_strip_relay_recursive_flattens_nested_connections():
    data = {"edges": [{"node": {"children": {"edges": [{"node": {"id": 9}}]}}}]}

    result = strip_relay(data, recursive=True)

    assert result == [{"children": [{"id": 9}]}]


def test_strip_relay_passes_scalars_through():
    assert strip_relay(7) == 7
    assert strip_relay("x") == "x"


def test_strip_relay_recurses_into_plain_dicts():
    data = {"meta": {"total": 3}, "items": {"edges": [{"node": {"id": 1}}]}}

    assert strip_relay(data, recursive=True) == {"meta": {"total": 3}, "items": [{"id": 1}]}
