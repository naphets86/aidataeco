from datetime import date, datetime
from fractions import Fraction

import pytest

from src.parsing import (as_bool, as_date, as_fraction, as_int, as_list, as_mapping, as_text,
                         check_keys, optional)


def test_container_types_are_checked():
    assert as_mapping("x", {"a": 1}) == {"a": 1}
    assert as_list("x", [1]) == [1]
    assert as_list("x", (1, 2)) == [1, 2]
    with pytest.raises(ValueError, match="x muss ein Mapping sein"):
        as_mapping("x", [1])
    with pytest.raises(ValueError, match="x muss eine Liste sein"):
        as_list("x", "abc")


def test_check_keys_reports_missing_and_unknown_fields():
    check_keys("s", {"a": 1, "b": 2}, ("a",), ("b",))
    check_keys("s", {})
    with pytest.raises(ValueError, match="s: Pflichtfeld fehlt: a"):
        check_keys("s", {"b": 2}, ("a",), ("b",))
    with pytest.raises(ValueError, match="s: Unbekannte Felder: 1, z"):
        check_keys("s", {"a": 1, "z": 2, 1: 3}, ("a",))


def test_scalars_are_checked():
    assert as_text("t", "a") == "a"
    assert as_bool("b", False) is False
    assert as_int("i", 3) == 3
    for parser, bad, message in ((as_text, 1, "Text"), (as_bool, 1, "true oder false"),
                                 (as_int, True, "ganze Zahl"), (as_int, 1.5, "ganze Zahl")):
        with pytest.raises(ValueError, match=message):
            parser("n", bad)


def test_fractions_are_exact_and_strict():
    assert as_fraction("f", 3) == 3
    assert as_fraction("f", 0.1) == Fraction(1, 10)
    assert as_fraction("f", "3/20") == Fraction(3, 20)
    assert as_fraction("f", Fraction(1, 3)) == Fraction(1, 3)
    for bad in (True, [1], None):
        with pytest.raises(ValueError, match="muss eine Zahl sein"):
            as_fraction("f", bad)
    for bad in ("abc", "1/0", float("inf"), float("nan")):
        with pytest.raises(ValueError, match="keine gültige Zahl"):
            as_fraction("f", bad)


def test_dates_accept_iso_text_and_reject_timestamps():
    assert as_date("d", date(2026, 1, 2)) == date(2026, 1, 2)
    assert as_date("d", "2026-01-02") == date(2026, 1, 2)
    with pytest.raises(ValueError, match="ohne Uhrzeit"):
        as_date("d", datetime(2026, 1, 2, 3, 4))
    with pytest.raises(ValueError, match="kein Datum"):
        as_date("d", "gestern")
    with pytest.raises(ValueError, match="muss ein Datum sein"):
        as_date("d", 20260102.5)


def test_optional_keeps_unknown_as_none():
    assert optional(as_int, "i", None) is None
    assert optional(as_int, "i", 4) == 4
    with pytest.raises(ValueError):
        optional(as_int, "i", "4")
