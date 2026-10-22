import dataclasses
import json
from fractions import Fraction

import pytest

from src.compare import Direction, compare_reports, direction
from src.evaluation import Evaluation
from src.governance import ReliabilityLevel
from src.report import NodeStatus, build_report
from src.spec import answers_for, parse_spec

from sample_data import Q2, TODAY, base_answers, base_data

VERSIONS = {"python": "3.11.0"}


def _report(data=None, answers=None, loss=5):
    spec = parse_spec(base_data() if data is None else data)
    return build_report(spec, answers_for(spec, base_answers() if answers is None else answers),
                        TODAY, loss, VERSIONS)


def _worse():
    answers = base_answers()
    answers[Q2]["value"] = 99
    del answers[Q2]["provenance"]
    data = base_data()
    data["network"]["nodes"][0]["updated"] = None
    data["network"]["nodes"][1]["quality"] = None
    data["network"]["edges"] = data["product"]["edges"] = []
    return _report(data, answers, loss=99)


def test_direction_orders_values_and_treats_missing_evidence_as_worst():
    assert direction(1, 1, True) is Direction.UNCHANGED
    assert direction(None, None, False) is Direction.UNCHANGED
    assert direction(1, 2, True) is Direction.IMPROVED
    assert direction(2, 1, True) is Direction.REGRESSED
    assert direction(2, 1, False) is Direction.IMPROVED
    assert direction(1, 2, False) is Direction.REGRESSED
    assert direction(Fraction(1, 2), None, True) is Direction.REGRESSED
    assert direction(3, None, False) is Direction.REGRESSED
    assert direction(None, Fraction(1, 2), True) is Direction.IMPROVED
    assert direction(None, 3, False) is Direction.IMPROVED


def test_identical_reports_show_no_regression():
    report = _report()
    comparison = compare_reports(report, report)
    assert not comparison.has_regression and comparison.regressions == ()
    assert all(change.direction is Direction.UNCHANGED for change in comparison.changes)
    assert comparison.new_blockers == () and comparison.resolved_blockers == ()
    assert not comparison.fingerprint_changed


def test_degradation_is_reported_per_metric_and_as_new_blockers():
    good, bad = _report(), _worse()
    comparison = compare_reports(good, bad)
    assert comparison.has_regression
    assert {c.metric for c in comparison.regressions} == {
        "Bestehensquote", "Provenance-Abdeckung", "Offene Verknüpfungen",
        "Knoten ohne Aktualitätsnachweis", "Knoten ohne bekannte Qualität", "Freigabehindernisse"}
    assert comparison.new_blockers and comparison.resolved_blockers == ()
    assert comparison.fingerprint_changed
    improved = compare_reports(bad, good)
    assert not improved.has_regression
    assert improved.resolved_blockers == comparison.new_blockers
    assert {c.metric for c in improved.changes if c.direction is Direction.IMPROVED} \
        == {c.metric for c in comparison.regressions}


def test_a_replaced_blocker_counts_as_regression_even_with_equal_counts():
    first = dataclasses.replace(_report(), blockers=("a",))
    second = dataclasses.replace(first, blockers=("b",))
    comparison = compare_reports(first, second)
    assert comparison.regressions == () and comparison.has_regression
    assert comparison.new_blockers == ("b",) and comparison.resolved_blockers == ("a",)


def test_lost_evaluation_is_a_regression_and_a_new_one_an_improvement():
    report = _report()
    bare = dataclasses.replace(report, evaluation=None)
    assert compare_reports(report, bare).has_regression
    assert not compare_reports(bare, report).has_regression


def test_reports_of_different_products_are_not_comparable():
    other = dataclasses.replace(_report(), product="Anderes Produkt")
    with pytest.raises(ValueError, match="nicht vergleichbar"):
        compare_reports(_report(), other)


def test_comparison_is_rendered_as_markdown_and_json():
    good, bad = _report(), _worse()
    text = compare_reports(good, bad).to_markdown()
    assert text.startswith("# Vergleich: Sales Result 360\n")
    assert "**Regression festgestellt.**" in text
    assert "| Bestehensquote | 1 | 1/4 | verschlechtert |" in text
    assert "## Neue Freigabehindernisse" in text and "## Behobene Freigabehindernisse" not in text
    back = compare_reports(bad, good).to_markdown()
    assert "Keine Regression." in back and "## Behobene Freigabehindernisse" in back
    bare = compare_reports(dataclasses.replace(good, evaluation=None), good).to_markdown()
    assert "| Bestehensquote | nicht belegt | 1 | verbessert |" in bare
    gone = compare_reports(good, dataclasses.replace(good, evaluation=None)).to_markdown()
    assert "| Bestehensquote | 1 | nicht belegt | verschlechtert |" in gone
    data = json.loads(compare_reports(good, bad).to_json())
    assert data["has_regression"] is True and data["level_before"] == "DECISION_PREPARATION"
    assert {"metric": "Bestehensquote", "before": "1", "after": "1/4",
            "direction": "REGRESSED"} in data["changes"]
    nothing = compare_reports(dataclasses.replace(good, evaluation=None), dataclasses.replace(
        good, evaluation=None)).to_dict()
    assert nothing["changes"][0] == {"metric": "Bestehensquote", "before": None, "after": None,
                                     "direction": "UNCHANGED"}
