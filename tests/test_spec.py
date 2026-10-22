import json
import sys
from datetime import date
from fractions import Fraction

import pytest

from src.errorbudget import ErrorBudget
from src.governance import ReliabilityLevel
from src.model import Answer
from src.spec import (MEASURED, ORGANIZATIONAL, answers_for, load_spec, parse_answers, parse_spec,
                      read_document)

from sample_data import Q1, Q2, as_json, base_answers, base_data


def test_parse_spec_builds_the_model_objects():
    spec = parse_spec(base_data())
    product = spec.product
    assert product.name == "Sales Result 360"
    assert product.node_names == frozenset({"orders", "freight"})
    assert product.network.node("orders").quality == Fraction(9, 10)
    assert product.network.node("orders").updated == date(2026, 10, 20)
    assert product.network.node("freight").updated == date(2026, 10, 21)
    assert product.label.version == "1.0" and product.label.frequency_days == 7
    assert product.meaning.resolve("Marge") == "DB I abzüglich Fracht"
    assert spec.required_links == (("orders", "freight"),)
    assert spec.kpis == ("Marge",)
    assert spec.accountabilities.missing() == ()
    use_case = spec.use_case
    assert use_case.level is ReliabilityLevel.DECISION_PREPARATION
    assert use_case.budget == ErrorBudget(100, Fraction(1, 10))
    assert use_case.min_pass_rate == Fraction(1, 2)
    assert [case.weight for case in use_case.cases] == [1, 3]
    assert spec.declared.human_decides and not spec.declared.kpis_defined
    assert spec.raw == base_data()


def test_optional_sections_are_never_filled_with_implicit_values():
    data = base_data()
    for key in ("accountabilities", "evidence"):
        del data[key]
    del data["network"]["edges"], data["product"]["edges"]
    for key in ("required_links", "kpis"):
        del data["product"][key]
    for key in ("error_budget", "min_pass_rate", "reference_cases"):
        del data["use_case"][key]
    data["product"]["nodes"] = []
    spec = parse_spec(data)
    assert spec.accountabilities.missing() == ("Data Owner", "Data Product Owner", "Use-Case Owner")
    assert not any(vars(spec.declared).values())
    assert spec.product.edges == () and spec.required_links == () and spec.kpis == ()
    assert spec.use_case.budget is None and spec.use_case.min_pass_rate is None
    assert spec.use_case.cases == ()


def test_level_accepts_numbers_and_names():
    for given, expected in ((1, ReliabilityLevel.HINT), (4, ReliabilityLevel.AUTOMATED_ACTION),
                            ("CROSS_CHECK", ReliabilityLevel.CROSS_CHECK)):
        data = base_data()
        data["use_case"]["level"] = given
        assert parse_spec(data).use_case.level is expected


def _set(path, value):
    def mutate(data):
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
    return mutate


def _delete(path):
    def mutate(data):
        target = data
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]
    return mutate


@pytest.mark.parametrize("mutate,message", [
    (_set(["unbekannt"], 1), "Unbekannte Felder: unbekannt"),
    (_delete(["network"]), "Pflichtfeld fehlt: network"),
    (_set(["network", "nodes", 0, "attributes"], "x"), "muss eine Liste sein"),
    (_set(["network", "nodes", 0, "quality"], 2), r"\[0, 1\]"),
    (_set(["network", "nodes", 0, "updated"], "morgen"), "kein Datum"),
    (_set(["network", "nodes", 0, "extra"], 1), "Unbekannte Felder: extra"),
    (_set(["network", "nodes", 1, "name"], "orders"), "eindeutig"),
    (_set(["network", "edges", 0, "target"], "fehlt"), "unbekannten Knoten"),
    (_delete(["network", "edges", 0, "transformation"]), "Pflichtfeld fehlt: transformation"),
    (_set(["product", "nodes"], ["orders", "fehlt"]), "Teilmenge"),
    (_set(["product", "edges"], [{"source": "freight", "target": "orders", "transformation": "t"}]),
     "Teilmenge"),
    (_set(["product", "meaning", "definitions"], ["x"]), "muss ein Mapping sein"),
    (_set(["product", "meaning", "synonyms"], {"a": 1}), "muss ein Text sein"),
    (_set(["product", "label", "version"], 1.2), "muss ein Text sein"),
    (_set(["product", "label", "frequency_days"], "7"), "ganze Zahl"),
    (_set(["product", "label", "frequency_days"], 0), "positiv"),
    (_set(["product", "label", "owner"], " "), "Owner"),
    (_set(["product", "required_links"], [["a"]]), "genau zwei Knoten"),
    (_set(["product", "kpis"], [1]), "muss ein Text sein"),
    (_set(["accountabilities", "chef"], "X"), "Unbekannte Felder: chef"),
    (_set(["accountabilities", "data_owner"], 3), "muss ein Text sein"),
    (_set(["use_case", "level"], 5), "Stufe muss 1 bis 4 sein"),
    (_set(["use_case", "level"], "FOO"), "Unbekannte Stufe 'FOO'"),
    (_set(["use_case", "level"], True), "muss eine Stufe sein"),
    (_set(["use_case", "level"], 2.5), "muss eine Stufe sein"),
    (_set(["use_case", "error_budget", "epsilon"], 0), "positiv"),
    (_delete(["use_case", "error_budget", "stakes"]), "Pflichtfeld fehlt: stakes"),
    (_set(["use_case", "min_pass_rate"], 2), r"\[0, 1\]"),
    (_set(["use_case", "reference_cases", 1, "question"], Q1), "eindeutig"),
    (_set(["use_case", "reference_cases", 1, "tolerance"], -1), "nichtnegativ"),
    (_set(["evidence", "provenance_available"], True), "gemessen.*provenance_available"),
    (_set(["evidence", "wunsch"], True), "Unbekannte Felder: wunsch"),
    (_set(["evidence", "logging"], "ja"), "true oder false"),
])
def test_invalid_specifications_are_rejected(mutate, message):
    data = base_data()
    mutate(data)
    with pytest.raises(ValueError, match=message):
        parse_spec(data)


def test_reference_cases_need_a_positive_total_weight():
    data = base_data()
    for case in data["use_case"]["reference_cases"]:
        case["weight"] = 0
    with pytest.raises(ValueError, match="Summe der Gewichte"):
        parse_spec(data)


def test_measured_and_organizational_evidence_do_not_overlap():
    assert set(MEASURED).isdisjoint(ORGANIZATIONAL)
    assert len(MEASURED) + len(ORGANIZATIONAL) == 8


def test_read_document_reads_json_and_rejects_other_formats(tmp_path):
    path = tmp_path / "spec.json"
    path.write_text(as_json(base_data()), encoding="utf-8")
    assert read_document(path) == json.loads(as_json(base_data()))
    assert load_spec(path).product.name == "Sales Result 360"
    with pytest.raises(ValueError, match="Unbekanntes Dateiformat '.txt'"):
        read_document(tmp_path / "spec.txt")
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="spec.json muss ein Mapping sein"):
        read_document(path)
    path.write_text("{kaputt", encoding="utf-8")
    with pytest.raises(ValueError):
        read_document(path)


def test_read_document_reads_yaml(tmp_path):
    pytest.importorskip("yaml")
    path = tmp_path / "spec.yaml"
    path.write_text("a: 1\nd: 2026-10-20\n", encoding="utf-8")
    assert read_document(path) == {"a": 1, "d": date(2026, 10, 20)}
    path.write_text("a: [", encoding="utf-8")
    with pytest.raises(ValueError, match="ungültiges YAML"):
        read_document(path)


def test_read_document_names_the_missing_yaml_dependency(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "yaml", None)
    path = tmp_path / "spec.yml"
    path.write_text("a: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="benötigt PyYAML"):
        read_document(path)


def test_parse_answers_reads_values_and_provenance():
    answers = parse_answers(base_answers())
    assert answers[Q2].value == 21
    provenance = answers[Q1].provenance
    assert provenance.sources == (("orders", "1.0"),)
    assert provenance.cutoff == date(2026, 10, 21)
    assert provenance.rules == ("DB II",)
    assert provenance.is_complete()
    sparse = parse_answers({"q": {"value": None}, "r": {"value": 1, "provenance": {}}})
    assert sparse["q"] == Answer(None, None)
    assert sparse["r"].provenance.missing() == ("Quelle", "Datenstichtag", "Definition")


@pytest.mark.parametrize("data,message", [
    ({"q": 1}, "Antwort zu 'q' muss ein Mapping sein"),
    ({"q": {}}, "Pflichtfeld fehlt: value"),
    ({"q": {"value": "x"}}, "keine gültige Zahl"),
    ({"q": {"value": 1, "wert": 2}}, "Unbekannte Felder: wert"),
    ({1: {"value": 1}}, "Frage muss ein Text sein"),
    ({"q": {"value": 1, "provenance": {"sources": [["nur-eine"]]}}}, "muss .Quelle, Version. sein"),
    ({"q": {"value": 1, "provenance": {"cutoff": "x"}}}, "kein Datum"),
    ({"q": {"value": 1, "provenance": {"quelle": []}}}, "Unbekannte Felder: quelle"),
])
def test_invalid_answers_are_rejected(data, message):
    with pytest.raises(ValueError, match=message):
        parse_answers(data)


def test_answers_for_follows_case_order_and_marks_missing_questions():
    spec = parse_spec(base_data())
    data = base_answers()
    assert [a.value for a in answers_for(spec, data)] == [10, 21]
    del data[Q1]
    assert answers_for(spec, data)[0] == Answer(None)
    data["Tippfehler"] = {"value": 1}
    with pytest.raises(ValueError, match="unbekannten Fragen: Tippfehler"):
        answers_for(spec, data)
