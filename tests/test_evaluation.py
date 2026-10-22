from datetime import date
from fractions import Fraction

import pytest

from src.evaluation import (
    Cause,
    ReferenceCase,
    attribute_completeness,
    evaluate,
    explained_share,
    is_fresh,
    provenance_coverage,
    weighted_pass_rate,
)
from src.model import Answer, Provenance

COMPLETE = Provenance((("p", "1"),), date(2026, 9, 30), ("Regel",))


def test_reference_case_validates_and_judges_with_tolerance():
    case = ReferenceCase("Marge Q3?", 24, Fraction(1, 2))
    assert case.weight == 1
    assert case.passed(Answer(Fraction(47, 2)))
    assert case.passed(Answer(Fraction(49, 2)))
    assert not case.passed(Answer(Fraction(51, 2)))
    assert not case.passed(Answer(None))
    with pytest.raises(ValueError, match="Frage"):
        ReferenceCase(" ", 1, 0)
    with pytest.raises(ValueError, match="nichtnegativ"):
        ReferenceCase("q", 1, -1)
    with pytest.raises(ValueError, match="nichtnegativ"):
        ReferenceCase("q", 1, 0, -1)


def test_weighted_pass_rate_follows_the_formula_of_the_paper():
    cases = [ReferenceCase("a", 10, 1, 3), ReferenceCase("b", 20, 1, 1), ReferenceCase("c", 5, 0, 0)]
    answers = [Answer(10), Answer(30), Answer(99)]
    assert weighted_pass_rate(cases, answers) == Fraction(3, 4)
    assert weighted_pass_rate(cases[:1], [Answer(None)]) == 0


def test_weighted_pass_rate_rejects_invalid_input():
    case = ReferenceCase("a", 1, 0)
    with pytest.raises(ValueError, match="gleich viele"):
        weighted_pass_rate([case], [])
    with pytest.raises(ValueError, match="Gewichte"):
        weighted_pass_rate([ReferenceCase("a", 1, 0, 0)], [Answer(1)])


def test_provenance_coverage_counts_only_complete_provenance():
    answers = [Answer(1, COMPLETE), Answer(2), Answer(3, Provenance()), Answer(4, COMPLETE)]
    assert provenance_coverage(answers) == Fraction(1, 2)
    with pytest.raises(ValueError, match="Antwort"):
        provenance_coverage([])


def test_explained_share_matches_the_case_study_and_partial_explanations():
    causes = [Cause("Fracht", 230, 0), Cause("Mix", 150, 0), Cause("Rabatte", 60, 1)]
    assert explained_share(causes) == Fraction(3, 22)
    assert explained_share([Cause("a", 100, Fraction(1, 2))]) == Fraction(1, 2)
    assert explained_share(causes, 880) == Fraction(3, 44)
    with pytest.raises(ValueError, match="positiv"):
        explained_share([])
    with pytest.raises(ValueError, match="opt"):
        explained_share([Cause("a", 100, 1)], 50)


def test_cause_validates_amounts_and_shares():
    assert Cause("x", 0.5, 0.25).amount == Fraction(1, 2)
    with pytest.raises(ValueError, match="Betrag"):
        Cause("x", -1, 0)
    with pytest.raises(ValueError, match="Erklärter Anteil"):
        Cause("x", 1, 2)


def test_attribute_completeness_treats_empty_values_as_missing():
    rows = [{"gruppe": "A"}, {"gruppe": None}, {"gruppe": "  "}, {}, {"gruppe": 0}, {"gruppe": "B"}]
    assert attribute_completeness(rows, "gruppe") == Fraction(1, 2)
    assert attribute_completeness(iter([{"x": 1}]), "x") == 1
    with pytest.raises(ValueError, match="Zeile"):
        attribute_completeness([], "x")


def test_freshness_treats_unknown_and_future_dates_as_not_fresh():
    today = date(2026, 10, 15)
    assert is_fresh(date(2026, 10, 14), 1, today)
    assert is_fresh(today, 1, today)
    assert not is_fresh(date(2026, 10, 13), 1, today)
    assert not is_fresh(None, 7, today)
    assert not is_fresh(date(2026, 10, 16), 7, today)
    with pytest.raises(ValueError, match="positiv"):
        is_fresh(today, 0, today)


def test_evaluate_reports_metrics_separately():
    cases = [ReferenceCase("a", 1, 0), ReferenceCase("b", 2, 0)]
    result = evaluate(cases, [Answer(1, COMPLETE), Answer(None)])
    assert result.pass_rate == Fraction(1, 2)
    assert result.provenance_coverage == Fraction(1, 2)
    assert result.unanswered == 1
