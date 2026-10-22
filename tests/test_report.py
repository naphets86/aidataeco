import dataclasses
import json
from datetime import date
from fractions import Fraction

import pytest

from src.evaluation import Evaluation
from src.governance import Evidence, ReliabilityLevel
from src.model import Answer
from src.report import EVIDENCE_LABELS, GoLiveReport, NodeStatus, build_report
from src.spec import answers_for, load_spec, parse_spec, read_document

from sample_data import Q1, Q2, TODAY, base_answers, base_data

VERSIONS = {"python": "3.11.0", "subgraph-sat-solver-econ": None}


def _report(data=None, answers=None, loss=5, today=TODAY, versions=VERSIONS):
    spec = parse_spec(base_data() if data is None else data)
    given = base_answers() if answers is None else answers
    return build_report(spec, answers_for(spec, given), today, loss, versions)


def test_complete_specification_has_no_blockers():
    report = _report()
    assert report.blockers == () and not report.blocked
    assert all(getattr(report.evidence, f.name) for f in dataclasses.fields(Evidence))
    assert report.evaluation == Evaluation(Fraction(1), Fraction(1), 0)
    assert report.budget_limit == 10 and report.expected_loss == 5
    assert report.product == "Sales Result 360" and report.version == "1.0" and report.owner == "Controlling"
    assert [node.name for node in report.nodes] == ["freight", "orders"]
    assert report.nodes[1] == NodeStatus("orders", Fraction(9, 10), date(2026, 10, 20), True)
    assert len(report.fingerprint) == 64


def test_automated_action_needs_the_declared_organizational_evidence():
    data = base_data()
    data["use_case"]["level"] = 4
    assert _report(data).blockers == ()
    data["evidence"] = {}
    blockers = _report(data).blockers
    assert "Nachweis fehlt: Ausdrückliche Freigabe liegt vor" in blockers
    assert len(blockers) == 3


def test_measured_evidence_is_derived_never_declared():
    data = base_data()
    data["network"]["nodes"][0]["quality"] = None
    report = _report(data)
    assert not report.evidence.quality_measurable
    assert "Nachweis fehlt: Qualität ist messbar" in report.blockers


def test_error_budget_needs_a_measured_loss_within_the_limit():
    assert _report(loss=10).evidence.error_budget_met
    over = _report(loss=11)
    assert not over.evidence.error_budget_met
    assert "Nachweis fehlt: Error Budget ist für den Anwendungsfall eingehalten" in over.blockers
    assert not _report(loss=None).evidence.error_budget_met
    with pytest.raises(ValueError, match="nichtnegativ"):
        _report(loss=-1)
    data = base_data()
    del data["use_case"]["error_budget"]
    assert not _report(data, loss=None).evidence.error_budget_met
    with pytest.raises(ValueError, match="ohne Error Budget"):
        _report(data, loss=1)


def test_pass_rate_below_the_minimum_blocks():
    answers = base_answers()
    answers[Q2]["value"] = 99
    report = _report(answers=answers)
    assert report.evaluation.pass_rate == Fraction(1, 4)
    assert "Bestehensquote 1/4 liegt unter dem Mindestwert 1/2" in report.blockers
    data = base_data()
    del data["use_case"]["min_pass_rate"]
    assert _report(data, answers).blockers == ()


def test_missing_answers_and_provenance_are_not_success():
    answers = base_answers()
    del answers[Q2]
    answers[Q1]["provenance"] = {"sources": [["orders", "1.0"]]}
    report = _report(answers=answers)
    assert report.evaluation.unanswered == 1
    assert report.evaluation.provenance_coverage == Fraction(0)
    assert not report.evidence.provenance_available
    assert "Nachweis fehlt: Quelle, Definition und Zeitstempel sind verfügbar" in report.blockers


def test_without_reference_cases_nothing_is_demonstrated():
    data = base_data()
    del data["use_case"]["reference_cases"]
    spec = parse_spec(data)
    report = build_report(spec, (), TODAY, None, VERSIONS)
    assert report.evaluation is None and not report.evidence.provenance_available
    assert "Nachweis fehlt: Bestehensquote (keine Referenzfälle)" in report.blockers
    del data["use_case"]["min_pass_rate"]
    assert "Bestehensquote" not in " ".join(build_report(parse_spec(data), (), TODAY, None, VERSIONS).blockers)
    with pytest.raises(ValueError, match="Antworten ohne Referenzfälle"):
        build_report(spec, (Answer(1),), TODAY)
    with pytest.raises(ValueError, match="gleich viele"):
        build_report(parse_spec(base_data()), (Answer(1),), TODAY)


def test_freshness_is_required_from_level_three_on():
    data = base_data()
    data["network"]["nodes"][0]["updated"] = "2026-10-01"
    data["network"]["nodes"][1]["updated"] = None
    report = _report(data)
    assert [n.fresh for n in report.nodes] == [None, False]
    assert report.blockers == ("Aktualität nicht belegt: freight", "Aktualität nicht belegt: orders")
    data["use_case"]["level"] = "CROSS_CHECK"
    assert _report(data).blockers == ()
    future = base_data()
    future["network"]["nodes"][0]["updated"] = "2026-10-30"
    assert "Aktualität nicht belegt: orders" in _report(future).blockers


def test_links_kpis_and_roles_gate_the_release():
    data = base_data()
    data["network"]["edges"] = data["product"]["edges"] = []
    report = _report(data)
    assert report.missing_links == (("orders", "freight"),)
    assert not report.evidence.kpis_defined
    for change in (lambda d: d["product"].update(kpis=[]),
                   lambda d: d["product"].update(kpis=["Gewinn"])):
        data = base_data()
        change(data)
        data["product"]["edges"] = []
        data["product"]["required_links"] = []
        assert not _report(data).evidence.kpis_defined
    data = base_data()
    data["product"]["nodes"] = []
    data["product"]["edges"] = []
    data["product"]["required_links"] = []
    assert not _report(data).evidence.quality_measurable
    data = base_data()
    del data["accountabilities"]["use_case_owner"]
    assert _report(data).blockers == ("Keine verantwortliche Person benannt: Use-Case Owner",)


def test_fingerprint_binds_all_inputs_but_not_the_result():
    base = _report()
    assert base.fingerprint == _report().fingerprint
    answers = base_answers()
    answers[Q1]["value"] = 11
    data = base_data()
    data["product"]["label"]["version"] = "2.0"
    variants = (_report(answers=answers), _report(loss=6), _report(today=date(2026, 10, 23)),
                _report(data), _report(versions={"python": "3.12.0"}))
    assert len({base.fingerprint, *(v.fingerprint for v in variants)}) == 6


def test_default_versions_are_collected():
    spec = parse_spec(base_data())
    report = build_report(spec, answers_for(spec, base_answers()), TODAY)
    assert "python" in report.versions and "subgraph-sat-solver-econ" in report.versions


def test_report_round_trips_through_json():
    for report in (_report(), _report(loss=None), _report(loss=99)):
        text = report.to_json()
        assert text.endswith("}\n")
        assert GoLiveReport.from_dict(json.loads(text)) == report
    data = base_data()
    data["network"]["edges"] = data["product"]["edges"] = []
    unlinked = _report(data)
    assert unlinked.missing_links and GoLiveReport.from_dict(json.loads(unlinked.to_json())) == unlinked
    data = base_data()
    del data["use_case"]["reference_cases"], data["use_case"]["error_budget"], data["use_case"]["min_pass_rate"]
    data["network"]["nodes"][0]["updated"] = None
    bare = build_report(parse_spec(data), (), TODAY, None, VERSIONS)
    assert GoLiveReport.from_dict(json.loads(bare.to_json())) == bare
    assert bare.to_dict()["evaluation"] is None


def _stored(**changes):
    data = json.loads(_report().to_json())
    data.update(changes)
    return data


@pytest.mark.parametrize("changes,message", [
    ({"extra": 1}, "Unbekannte Felder: extra"),
    ({"level": "FOO"}, "Unbekannte Stufe"),
    ({"level": 3}, "Unbekannte Stufe"),
    ({"missing_links": [["a"]]}, "zwei Knoten"),
    ({"nodes": [{"name": "a", "quality": None, "updated": None, "fresh": "ja"}]}, "true oder false"),
    ({"evaluation": {"pass_rate": "1", "provenance_coverage": "1", "unanswered": "0"}}, "ganze Zahl"),
    ({"evidence": {"logging": True}}, "Pflichtfeld fehlt"),
    ({"blocked": True}, "blocked passt nicht zu blockers"),
    ({"versions": {"python": 3}}, "muss ein Text sein"),
    ({"today": "heute"}, "kein Datum"),
])
def test_stored_reports_are_read_strictly(changes, message):
    with pytest.raises(ValueError, match=message):
        GoLiveReport.from_dict(_stored(**changes))


def test_markdown_lists_blockers_metrics_evidence_and_nodes():
    answers = base_answers()
    answers[Q2]["value"] = 99
    data = base_data()
    data["network"]["nodes"][0]["name"] = "or|ders"
    data["network"]["edges"][0]["source"] = "or|ders"
    data["product"]["nodes"] = ["or|ders", "freight"]
    data["product"]["edges"][0]["source"] = "or|ders"
    data["product"]["required_links"] = [["or|ders", "freight"], ["freight", "freight2"]]
    text = _report(data, answers).to_markdown()
    assert text.startswith("# Freigabebericht: Sales Result 360\n")
    assert "**2 Freigabehindernis(se)** für Stufe 3." in text
    assert "| Bestehensquote | 1/4 (25,0 %) |" in text
    assert "| Zulässiger Verlust ε·W | 10 |" in text
    assert "| Kennzahlen definiert und verknüpft | nicht belegt |" in text
    assert "| or\\|ders | 9/10 (90,0 %) | 2026-10-20 | ja |" in text
    assert "## Offene Verknüpfungen" in text and "- freight ↔ freight2" in text
    assert "- subgraph-sat-solver-econ: nicht installiert" in text


def test_markdown_for_clean_and_unevidenced_reports():
    clean = _report().to_markdown()
    assert "kein Freigabehindernis festgestellt. Das ist keine automatische Freigabe" in clean
    assert "## Offene Verknüpfungen" not in clean and "**" not in clean.split("## Kennzahlen")[0]
    assert set(EVIDENCE_LABELS) == {f.name for f in dataclasses.fields(Evidence)}
    data = base_data()
    for key in ("reference_cases", "error_budget", "min_pass_rate"):
        del data["use_case"][key]
    data["network"]["nodes"][0]["quality"] = None
    data["network"]["nodes"][0]["updated"] = None
    bare = build_report(parse_spec(data), (), TODAY, None, VERSIONS).to_markdown()
    assert "| Bestehensquote | nicht belegt (keine Referenzfragen) |" in bare
    assert "| Provenance-Abdeckung | nicht belegt (keine Referenzfragen) |" in bare
    assert "| Mindest-Bestehensquote | nicht festgelegt |" in bare
    assert "| Erwarteter Verlust | nicht belegt |" in bare
    assert "| Zulässiger Verlust ε·W | nicht festgelegt |" in bare
    assert "| orders | unbekannt | unbekannt | unbekannt |" in bare
    assert "| freight | 4/5 (80,0 %) | 2026-10-21 | ja |" in bare
    stale = base_data()
    stale["network"]["nodes"][0]["updated"] = "2026-01-01"
    assert "| 2026-01-01 | nein |" in _report(stale).to_markdown()


def test_example_specification_reproduces_the_case_study():
    pytest.importorskip("yaml")
    spec = load_spec("examples/sales_result_360.yaml")
    answers = answers_for(spec, read_document("examples/answers_sales_result_360.json"))
    report = build_report(spec, answers, date(2026, 10, 22), 380, VERSIONS)
    assert report.evaluation == Evaluation(Fraction(1, 6), Fraction(2, 3), 1)
    assert report.missing_links == (("orders", "freight"),)
    assert report.budget_limit == 22 and report.blocked
    assert report.evidence.human_decides and not report.evidence.error_budget_met
    assert "Bestehensquote 1/6 liegt unter dem Mindestwert 3/4" in report.blockers
    assert "Aktualität nicht belegt: products" in report.blockers
