"""Erschöpfende Prüfung der Eigenschaften, die die Arbeit im Abschnitt „Operationalisierung" beweist."""

import dataclasses
import itertools
from fractions import Fraction

from src.compare import Direction, compare_reports
from src.evaluation import Evaluation
from src.governance import Accountabilities, Evidence, ReliabilityLevel, release_blockers
from src.report import build_report
from src.spec import answers_for, parse_spec

from sample_data import TODAY, base_answers, base_data

FIELDS = [f.name for f in dataclasses.fields(Evidence)]
HUMAN = "Nachweis fehlt: Ein Mensch entscheidet"
ROLES = Accountabilities("a", "b", "c")


def _all_evidence():
    for bits in itertools.product((False, True), repeat=len(FIELDS)):
        yield bits, Evidence(**dict(zip(FIELDS, bits)))


def test_blockers_shrink_when_evidence_grows():
    """Satz (Antitonie): e ≤ e' ⇒ B(ℓ, e') ⊆ B(ℓ, e), für jede Stufe und jede Rollenbesetzung."""
    everything = list(_all_evidence())
    for level in ReliabilityLevel:
        for roles in (ROLES, Accountabilities()):
            for bits, evidence in everything:
                lower = set(release_blockers(level, roles, evidence))
                for bits2, evidence2 in everything:
                    if all(x <= y for x, y in zip(bits, bits2)):
                        assert set(release_blockers(level, roles, evidence2)) <= lower


def test_blockers_grow_with_the_level_except_for_the_oversight_requirement():
    """Satz (Stufenmonotonie): ℓ ≤ ℓ' ⇒ B(ℓ) ∖ {Mensch entscheidet} ⊆ B(ℓ') ∖ {Mensch entscheidet}."""
    levels = list(ReliabilityLevel)
    for _, evidence in _all_evidence():
        for low, high in itertools.combinations(levels, 2):
            lower = set(release_blockers(low, ROLES, evidence)) - {HUMAN}
            upper = set(release_blockers(high, ROLES, evidence)) - {HUMAN}
            assert lower <= upper


def test_the_oversight_requirement_applies_exactly_on_level_three():
    for _, evidence in _all_evidence():
        for level in ReliabilityLevel:
            expected = level == ReliabilityLevel.DECISION_PREPARATION and not evidence.human_decides
            assert (HUMAN in release_blockers(level, ROLES, evidence)) == expected


def _family():
    base = build_report(parse_spec(base_data()), answers_for(parse_spec(base_data()), base_answers()),
                        TODAY, 5, {"python": "3"})
    evaluations = (None, Evaluation(1, 1, 0), Evaluation(1, 1, 1), Evaluation(Fraction(1, 2), 1, 0))
    reports = []
    for evaluation, links, blockers in itertools.product(
            evaluations, ((), (("a", "b"),)), ((), ("x",), ("x", "y"), ("y",))):
        reports.append(dataclasses.replace(base, evaluation=evaluation, missing_links=links,
                                           blockers=blockers))
    return reports


def test_comparison_is_reflexive():
    for report in _family():
        assert not compare_reports(report, report).has_regression


def test_absence_of_regression_is_transitive():
    reports = _family()
    clean = {(i, j) for i, a in enumerate(reports) for j, b in enumerate(reports)
             if not compare_reports(a, b).has_regression}
    for i, j in clean:
        for k in range(len(reports)):
            if (j, k) in clean:
                assert (i, k) in clean


def test_improvement_and_regression_are_mirror_images():
    reports = _family()
    swap = {Direction.IMPROVED: Direction.REGRESSED, Direction.REGRESSED: Direction.IMPROVED,
            Direction.UNCHANGED: Direction.UNCHANGED}
    for a, b in itertools.product(reports[::3], reports[1::3]):
        forward, backward = compare_reports(a, b), compare_reports(b, a)
        assert [swap[c.direction] for c in forward.changes] == [c.direction for c in backward.changes]
        assert forward.new_blockers == backward.resolved_blockers


def test_report_is_a_pure_function_of_its_inputs():
    spec = parse_spec(base_data())
    answers = answers_for(spec, base_answers())
    first = build_report(spec, answers, TODAY, 5, {"python": "3"})
    second = build_report(parse_spec(base_data()), answers_for(parse_spec(base_data()), base_answers()),
                          TODAY, 5, {"python": "3"})
    assert first == second and first.to_json() == second.to_json()
