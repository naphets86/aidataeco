"""Spezifikation, Freigabebericht, Referenzfragen und Berichtsvergleich über die Web-API."""

import copy
import json
from datetime import date

import pytest

from aidataeco.compare import compare_reports
from aidataeco.report import GoLiveReport, build_report
from aidataeco.spec import answers_for, parse_spec

from sample_data import TODAY, base_answers, base_data
from web_helpers import answers, client, jsonable, post, report_request, spec, url

pytestmark = pytest.mark.integration

VERSIONS = {"python": "3.11.0", "subgraph-sat-solver-econ": None}


def _library_report(data=None, given=None, loss=5):
    parsed = parse_spec(base_data() if data is None else data)
    return build_report(parsed, answers_for(parsed, base_answers() if given is None else given), TODAY, loss, VERSIONS)


def test_validate_spec_summarises_the_product():
    response = post("/specs/validate", {"spec": spec()})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["summary"]["product"] == "Sales Result 360"
    assert body["summary"]["level"] == "DECISION_PREPARATION" and body["summary"]["level_number"] == 3
    assert body["summary"]["nodes"] == ["freight", "orders"]
    assert body["summary"]["required_links"] == [["orders", "freight"]]
    assert body["summary"]["error_budget_limit"] == "10" and body["summary"]["min_pass_rate"] == "1/2"
    assert body["summary"]["missing_accountabilities"] == []
    assert body["summary"]["declared_evidence"]["human_decides"] is True


def test_validate_spec_reports_missing_roles_and_absent_optionals():
    data = spec()
    data["accountabilities"] = {"data_owner": "A"}
    del data["use_case"]["error_budget"], data["use_case"]["min_pass_rate"]
    summary = post("/specs/validate", {"spec": data}).json()["summary"]
    assert summary["missing_accountabilities"] == ["Data Product Owner", "Use-Case Owner"]
    assert summary["error_budget_limit"] is None and summary["min_pass_rate"] is None


@pytest.mark.parametrize("mutate,message", [
    (lambda d: d.pop("network"), "Pflichtfeld fehlt: network"),
    (lambda d: d.update(extra=1), "Unbekannte Felder: extra"),
    (lambda d: d["evidence"].update(error_budget_met=True), "darf nicht erklärt werden"),
    (lambda d: d["use_case"].update(level=7), "Stufe muss 1 bis 4 sein"),
    (lambda d: d["use_case"]["reference_cases"].append(copy.deepcopy(d["use_case"]["reference_cases"][0])),
     "eindeutig"),
])
def test_invalid_specs_are_422_input_errors(mutate, message):
    data = spec()
    mutate(data)
    response = post("/specs/validate", {"spec": data})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["type"] == "input_error" and message in error["message"]


def test_spec_with_huge_exponent_is_rejected_before_parsing():
    data = spec()
    data["network"]["nodes"][0]["quality"] = "1e999999999"
    response = post("/specs/validate", {"spec": data})
    assert response.status_code == 422 and "Exponenten" in response.json()["error"]["message"]


def test_report_matches_the_library_and_the_cli_json_shape():
    response = post("/reports", report_request())
    assert response.status_code == 200
    assert response.json() == json.loads(_library_report().to_json())


def test_clean_report_is_not_blocked_and_blocked_report_lists_blockers():
    assert post("/reports", report_request()).json()["blocked"] is False
    blocked = post("/reports", report_request(expected_loss=None)).json()
    assert blocked["blocked"] is True
    assert "Nachweis fehlt: Error Budget ist für den Anwendungsfall eingehalten" in blocked["blockers"]
    assert blocked["evidence"]["error_budget_met"] is False and blocked["expected_loss"] is None


def test_report_without_answers_leaves_questions_unanswered():
    body = report_request()
    del body["answers"]
    report = post("/reports", body).json()
    assert report["evaluation"] == {"pass_rate": "0", "provenance_coverage": "0", "unanswered": 2}
    assert report["blocked"] is True


def test_report_without_reference_cases_has_no_evaluation():
    data = spec()
    del data["use_case"]["reference_cases"], data["use_case"]["min_pass_rate"]
    report = post("/reports", report_request(spec=data, answers={})).json()
    assert report["evaluation"] is None and report["blocked"] is True


def test_expected_loss_may_be_a_fraction_text_or_a_float():
    assert post("/reports", report_request(expected_loss="9/2")).json()["expected_loss"] == "9/2"
    assert post("/reports", report_request(expected_loss=0.5)).json()["expected_loss"] == "1/2"


def test_report_fingerprint_depends_on_inputs_and_versions_but_is_reproducible():
    first = post("/reports", report_request()).json()["fingerprint"]
    assert post("/reports", report_request()).json()["fingerprint"] == first
    assert post("/reports", report_request(today="2026-10-23")).json()["fingerprint"] != first
    assert post("/reports", report_request(versions={"python": "3.12.0"})).json()["fingerprint"] != first


def test_report_without_versions_uses_server_versions():
    body = report_request()
    del body["versions"]
    versions = post("/reports", body).json()["versions"]
    assert "python" in versions and "subgraph-sat-solver-econ" in versions


@pytest.mark.parametrize("changes,message", [
    ({"today": "2026-02-30"}, "kein Datum"),
    ({"expected_loss": "abc"}, "keine gültige Zahl"),
    ({"expected_loss": "1e99999"}, "Exponenten"),
    ({"expected_loss": "1/0"}, "keine gültige Zahl"),
    ({"expected_loss": -1}, "nichtnegativ"),
    ({"answers": {"Unbekannt": {"value": 1}}}, "unbekannten Fragen"),
    ({"answers": {"Frage 1": {"value": 1, "extra": 2}}}, "Unbekannte Felder"),
    ({"answers": {"Frage 1": {"value": "9e99999"}}}, "Exponenten"),
])
def test_invalid_report_inputs_are_422_input_errors(changes, message):
    response = post("/reports", report_request(**changes))
    assert response.status_code == 422
    assert message in response.json()["error"]["message"]


def test_expected_loss_without_error_budget_is_an_input_error():
    data = spec()
    del data["use_case"]["error_budget"]
    response = post("/reports", report_request(spec=data))
    assert response.status_code == 422 and "ohne Error Budget" in response.json()["error"]["message"]


@pytest.mark.parametrize("body", [
    {"spec": spec(), "answers": {}},
    {"spec": spec(), "today": "22.10.2026"},
    {"spec": spec(), "today": "2026-10-22", "expected_loss": True},
    {"spec": [], "today": "2026-10-22"},
    {"spec": spec(), "today": "2026-10-22", "versions": {"python": 3}},
])
def test_malformed_report_requests_fail_request_validation(body):
    response = post("/reports", body)
    assert response.status_code == 422 and "detail" in response.json()


def test_report_markdown_equals_library_markdown():
    response = post("/reports/markdown", report_request())
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert response.text == _library_report().to_markdown()
    assert response.text.startswith("# Freigabebericht: Sales Result 360")


def test_report_markdown_errors_are_json_input_errors():
    response = post("/reports/markdown", report_request(today="2026-02-30"))
    assert response.status_code == 422 and response.json()["error"]["type"] == "input_error"


def test_cases_show_each_question_with_pass_and_provenance_status():
    given = answers()
    given["Frage 2"] = {"value": "30", "provenance": {"sources": [["orders", "1.0"]]}}
    del given["Frage 1"]["provenance"]
    body = post("/reports/cases", {"spec": spec(), "answers": given}).json()
    first, second = body["cases"]
    assert first["answered"] is True and first["passed"] is True
    assert first["provenance_complete"] is False
    assert first["provenance_missing"] == ["Quelle", "Datenstichtag", "Definition"]
    assert second["value"] == "30" and second["passed"] is False
    assert second["provenance_missing"] == ["Datenstichtag", "Definition"]
    assert body["evaluation"] == {"pass_rate": "1/4", "provenance_coverage": "0", "unanswered": 0}


def test_cases_handle_missing_answers_and_missing_reference_cases():
    body = post("/reports/cases", {"spec": spec()}).json()
    assert [case["value"] for case in body["cases"]] == [None, None]
    assert [case["passed"] for case in body["cases"]] == [False, False]
    data = spec()
    del data["use_case"]["reference_cases"], data["use_case"]["min_pass_rate"]
    assert post("/reports/cases", {"spec": data}).json() == {"cases": [], "evaluation": None}


def test_cases_reject_answers_to_unknown_questions():
    response = post("/reports/cases", {"spec": spec(), "answers": {"Tippfehler": {"value": 1}}})
    assert response.status_code == 422


def _two_reports():
    old = post("/reports", report_request(expected_loss=None)).json()
    new = post("/reports", report_request()).json()
    return old, new


def test_compare_reports_flags_improvement_and_regression_like_the_library():
    old, new = _two_reports()
    improved = post("/reports/compare", {"old": old, "new": new}).json()
    assert improved["has_regression"] is False
    assert "Nachweis fehlt: Error Budget ist für den Anwendungsfall eingehalten" in improved["resolved_blockers"]
    assert improved["fingerprint_changed"] is True
    expected = compare_reports(GoLiveReport.from_dict(old), GoLiveReport.from_dict(new)).to_dict()
    assert improved == expected
    regressed = post("/reports/compare", {"old": new, "new": old}).json()
    assert regressed["has_regression"] is True
    assert any(change["direction"] == "REGRESSED" for change in regressed["changes"])
    assert regressed["new_blockers"] == improved["resolved_blockers"]


def test_compare_markdown_equals_library_markdown():
    old, new = _two_reports()
    response = post("/reports/compare/markdown", {"old": old, "new": new})
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert response.text == compare_reports(GoLiveReport.from_dict(old), GoLiveReport.from_dict(new)).to_markdown()


def test_compare_rejects_different_products_and_malformed_reports():
    old, new = _two_reports()
    other = copy.deepcopy(new)
    other["product"] = "Anderes Produkt"
    response = post("/reports/compare", {"old": old, "new": other})
    assert response.status_code == 422 and "nicht vergleichbar" in response.json()["error"]["message"]
    assert post("/reports/compare", {"old": {}, "new": new}).status_code == 422
    broken = copy.deepcopy(new)
    broken["min_pass_rate"] = "1e99999"
    assert "Exponenten" in post("/reports/compare", {"old": old, "new": broken}).json()["error"]["message"]
    assert "Exponenten" in post("/reports/compare", {"old": broken, "new": new}).json()["error"]["message"]


def test_report_endpoint_is_stateless():
    first = client.post(url("/reports"), json=report_request()).json()
    client.post(url("/reports"), json=report_request(expected_loss=None))
    assert client.post(url("/reports"), json=report_request()).json() == first
    assert isinstance(TODAY, date)
