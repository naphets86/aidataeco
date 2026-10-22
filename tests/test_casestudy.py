from fractions import Fraction

import pytest

from src.casestudy import MarginCase, margin_case, margin_gap
from src.evaluation import Cause


def test_margin_case_reproduces_the_numbers_of_the_paper():
    case = margin_case()
    assert case.expected_db2 == 3080
    assert case.actual_db2 == 2640
    assert case.gap == 440
    assert [c.amount for c in case.causes] == [230, 150, 60]


def test_cause_shares_and_explained_share_match_the_paper():
    case = margin_case()
    shares = [round(float(c.amount / case.gap) * 100) for c in case.causes]
    assert shares == [52, 34, 14]
    assert case.explained_share == Fraction(3, 22)
    assert round(float(case.explained_share) * 100) == 14


def test_margin_gap_is_exact():
    assert margin_gap(11000, 0.28, 0.24) == 440
    assert margin_gap(10, Fraction(1, 2), Fraction(1, 2)) == 0


def test_causes_must_split_the_gap_exactly():
    with pytest.raises(ValueError, match="aufteilen"):
        MarginCase(Fraction(11000), Fraction(28, 100), Fraction(24, 100), (Cause("a", 100, 1),))
