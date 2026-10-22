import pytest

from src.governance import Accountabilities, Evidence, ReliabilityLevel, release_blockers

ALL = Accountabilities("Leitung Controlling", "Datenteam", "Fachbereich")


def _full_evidence(**overrides) -> Evidence:
    values = dict(
        kpis_defined=True, provenance_available=True, quality_measurable=True,
        error_budget_met=True, human_decides=True, explicit_approval=True,
        logging=True, intervention_path=True,
    )
    values.update(overrides)
    return Evidence(**values)


def test_levels_are_ordered():
    assert ReliabilityLevel.HINT < ReliabilityLevel.CROSS_CHECK < ReliabilityLevel.DECISION_PREPARATION
    assert ReliabilityLevel.AUTOMATED_ACTION == 4


def test_accountabilities_have_no_implicit_defaults():
    assert Accountabilities().missing() == ("Data Owner", "Data Product Owner", "Use-Case Owner")
    assert Accountabilities("a", " ", "c").missing() == ("Data Product Owner",)
    assert ALL.missing() == ()
    same_person = Accountabilities("Meier", "Meier", "Meier")
    assert same_person.missing() == ()


def test_hint_level_needs_only_named_owners():
    assert release_blockers(ReliabilityLevel.HINT, ALL, Evidence()) == []
    blockers = release_blockers(ReliabilityLevel.HINT, Accountabilities(), Evidence())
    assert len(blockers) == 3
    assert all("Keine verantwortliche Person" in b for b in blockers)


def test_cross_check_requires_defined_kpis():
    assert release_blockers(ReliabilityLevel.CROSS_CHECK, ALL, Evidence(kpis_defined=True)) == []
    blockers = release_blockers(ReliabilityLevel.CROSS_CHECK, ALL, Evidence())
    assert blockers == ["Nachweis fehlt: Zentrale Kennzahlen sind verknüpft und definiert"]


def test_decision_preparation_requires_evidence_and_a_human():
    ok = _full_evidence(explicit_approval=False, logging=False, intervention_path=False)
    assert release_blockers(ReliabilityLevel.DECISION_PREPARATION, ALL, ok) == []
    blockers = release_blockers(ReliabilityLevel.DECISION_PREPARATION, ALL, Evidence())
    assert len(blockers) == 5
    assert "Nachweis fehlt: Ein Mensch entscheidet" in blockers
    assert not any("Protokollierung" in b for b in blockers)


def test_automated_action_needs_approval_logging_and_intervention_path_but_no_human():
    assert release_blockers(ReliabilityLevel.AUTOMATED_ACTION, ALL, _full_evidence(human_decides=False)) == []
    blockers = release_blockers(ReliabilityLevel.AUTOMATED_ACTION, ALL, _full_evidence(logging=False))
    assert blockers == ["Nachweis fehlt: Protokollierung ist eingerichtet"]
    everything = release_blockers(ReliabilityLevel.AUTOMATED_ACTION, Accountabilities(), Evidence())
    assert len(everything) == 3 + 1 + 3 + 3


@pytest.mark.parametrize("level", list(ReliabilityLevel))
def test_missing_accountability_blocks_every_level(level):
    blockers = release_blockers(level, Accountabilities(data_owner="a"), _full_evidence())
    assert blockers == [
        "Keine verantwortliche Person benannt: Data Product Owner",
        "Keine verantwortliche Person benannt: Use-Case Owner",
    ]
