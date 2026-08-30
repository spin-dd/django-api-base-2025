"""Tests for `apibase.graphql.encoders.JSONEncode` (GQE-001)."""

import datetime
import decimal
import json

from apibase.graphql.encoders import JSONEncode


def test_json_encode_serializes_decimal_as_float():
    encoded = json.dumps({"price": decimal.Decimal("19.95")}, cls=JSONEncode)

    assert json.loads(encoded) == {"price": 19.95}


def test_json_encode_falls_back_to_django_encoder_for_dates():
    # DjangoJSONEncoder handles date/datetime; JSONEncode must not break it.
    encoded = json.dumps({"d": datetime.date(2024, 1, 2)}, cls=JSONEncode)

    assert json.loads(encoded) == {"d": "2024-01-02"}


def test_json_encode_handles_plain_types():
    encoded = json.dumps({"n": 1, "s": "x", "b": True}, cls=JSONEncode)

    assert json.loads(encoded) == {"n": 1, "s": "x", "b": True}
