"""Auswertung, Error Budget, Diagnose, Governance, Integration, Experimente und Fallstudie über die Web-API."""

import json
from fractions import Fraction

import pytest

import web.api as web_api
from aidataeco.casestudy import margin_case
from aidataeco.diagnosis import DeviationCause
from aidataeco.experiment import ExperimentRecord
from aidataeco.governance import Accountabilities, Evidence, ReliabilityLevel, release_blockers
from aidataeco.integration import IntegrationOption, select_integrations
from subgraph_sat_solver_econ.backends import BackendError

from web_helpers import client, post, url

pytestmark = pytest.mark.integration

PROVENANCE = {"sources": [["orders", "1.0"]], "cutoff": "2026-10-21", "rules": ["DB II"]}
CASES = [{"question": "F1", "reference": 10, "tolerance": 1},
         {"question": "F2", "reference": 20, "tolerance": 2, "weight": 3}]


def _error(response, status=422):
    assert response.status_code == status, response.text
    return response.json()["error"]["message"]


# ----------------------------------------------------------------------------- evaluation


def test_pass_rate_weights_answers_and_reports_provenance_separately():
    body = post("/evaluation/pass-rate", {
        "cases": CASES, "answers": {"F1": {"value": 10, "provenance": PROVENANCE}, "F2": {"value": "25"}}}).json()
    assert body["evaluation"] == {"pass_rate": "1/4", "provenance_coverage": "1/2", "unanswered": 0}
    assert [case["passed"] for case in body["cases"]] == [True, False]
    assert body["cases"][1]["weight"] == "3"


def test_pass_rate_treats_missing_and_null_answers_as_failed():
    body = post("/evaluation/pass-rate", {"cases": CASES, "answers": {"F1": {"value": None}}}).json()
    assert body["evaluation"] == {"pass_rate": "0", "provenance_coverage": "0", "unanswered": 2}
    assert post("/evaluation/pass-rate", {"cases": CASES}).json()["evaluation"]["unanswered"] == 2


def test_pass_rate_input_errors():
    assert "eindeutig" in _error(post("/evaluation/pass-rate", {"cases": CASES + CASES[:1]}))
    assert "unbekannten Fragen" in _error(post("/evaluation/pass-rate",
                                               {"cases": CASES, "answers": {"X": {"value": 1}}}))
    assert "Summe der Gewichte" in _error(post("/evaluation/pass-rate", {"cases": [
        {"question": "F", "reference": 1, "tolerance": 0, "weight": 0}]}))
    assert "Summe der Gewichte" in _error(post("/evaluation/pass-rate", {"cases": []}))
    assert "Exponenten" in _error(post("/evaluation/pass-rate", {"cases": [
        {"question": "F", "reference": "1e99999", "tolerance": 0}]}))
    assert "Exponenten" in _error(post("/evaluation/pass-rate", {
        "cases": CASES, "answers": {"F1": {"value": "1e99999"}}}))
    assert "kein Datum" in _error(post("/evaluation/pass-rate", {
        "cases": CASES, "answers": {"F1": {"value": 1, "provenance": {"cutoff": "2026-02-30"}}}}))
    assert post("/evaluation/pass-rate", {"cases": CASES, "answers": {"F1": {"value": 1, "provenance": {
        "sources": [["nur-eins"]]}}}}).status_code == 422


def test_explained_share_reproduces_the_case_study_value():
    body = post("/evaluation/explained-share", {"causes": [
        {"name": "Expressfracht", "amount": 230, "explained": 0},
        {"name": "Produktmix", "amount": 150, "explained": 0},
        {"name": "Rabatte", "amount": 60, "explained": 1}]}).json()
    assert body == {"explained_share": "3/22", "unexplained_share": "19/22", "explained_amount": "60",
                    "total_effect": "440"}


def test_explained_share_with_unassigned_remainder_and_errors():
    causes = [{"name": "A", "amount": 50, "explained": 1}]
    body = post("/evaluation/explained-share", {"causes": causes, "total_effect": 100}).json()
    assert body["explained_share"] == "1/2" and body["total_effect"] == "100"
    assert "A muss in" in _error(post("/evaluation/explained-share", {"causes": causes, "total_effect": 10}))
    assert "opt muss positiv" in _error(post("/evaluation/explained-share", {"causes": []}))
    assert "nichtnegativ" in _error(post("/evaluation/explained-share", {
        "causes": [{"name": "A", "amount": -1, "explained": 0}]}))
    assert "[0, 1]" in _error(post("/evaluation/explained-share", {
        "causes": [{"name": "A", "amount": 1, "explained": 2}]}))
    assert "Exponenten" in _error(post("/evaluation/explained-share", {"causes": causes, "total_effect": "1e9999"}))


def test_completeness_counts_none_empty_and_missing_values_as_unfilled():
    rows = [{"g": "A"}, {"g": ""}, {"g": "  "}, {"g": None}, {}, {"g": 0}]
    body = post("/evaluation/completeness", {"rows": rows, "attribute": "g"}).json()
    assert body == {"completeness": "1/3", "rows": 6, "filled": 2}
    assert "Mindestens eine Zeile" in _error(post("/evaluation/completeness", {"rows": [], "attribute": "g"}))


@pytest.mark.parametrize("updated,expected,age", [
    ("2026-10-15", True, 7), ("2026-10-14", False, 8), ("2026-10-23", False, -1), (None, False, None)])
def test_freshness(updated, expected, age):
    body = post("/evaluation/freshness", {"updated": updated, "frequency_days": 7, "today": "2026-10-22"}).json()
    assert body == {"fresh": expected, "age_days": age}


def test_freshness_input_errors():
    assert "positiv" in _error(post("/evaluation/freshness", {"updated": None, "frequency_days": 0,
                                                              "today": "2026-10-22"}))
    assert "kein Datum" in _error(post("/evaluation/freshness", {"updated": "2026-13-01", "frequency_days": 7,
                                                                 "today": "2026-10-22"}))
    assert "kein Datum" in _error(post("/evaluation/freshness", {"updated": None, "frequency_days": 7,
                                                                 "today": "2026-00-22"}))


# ----------------------------------------------------------------------------- error budget


def test_budget_check_good_enough_boundary_and_headroom():
    base = {"stakes": 440, "epsilon": "1/20"}
    inside = post("/error-budget/check", {**base, "expected_loss": 22}).json()
    assert inside == {"limit": "22", "expected_loss": "22", "good_enough": True, "headroom": "0"}
    over = post("/error-budget/check", {**base, "expected_loss": "45/2"}).json()
    assert over["good_enough"] is False and over["headroom"] == "-1/2"


def test_budget_input_errors():
    assert "Error Budget ε muss positiv" in _error(post("/error-budget/check", {
        "stakes": 1, "epsilon": 0, "expected_loss": 1}))
    assert "Stakes W" in _error(post("/error-budget/check", {"stakes": -1, "epsilon": 1, "expected_loss": 1}))
    assert "nichtnegativ" in _error(post("/error-budget/check", {"stakes": 1, "epsilon": 1, "expected_loss": -1}))
    assert post("/error-budget/check", {"stakes": 1, "epsilon": 1}).status_code == 422


def test_linear_loss_and_decomposition():
    body = post("/error-budget/linear-loss", {"cost_per_unit": 2, "expected_abs_error": 10, "stakes": 440,
                                              "epsilon": "1/20"}).json()
    assert body == {"expected_loss": "20", "limit": "22", "good_enough": True}
    assert post("/error-budget/linear-loss", {"cost_per_unit": 3, "expected_abs_error": 10, "stakes": 440,
                                              "epsilon": "1/20"}).json()["good_enough"] is False
    assert "nichtnegativ" in _error(post("/error-budget/linear-loss", {
        "cost_per_unit": -1, "expected_abs_error": 1, "stakes": 1, "epsilon": 1}))
    assert post("/error-budget/decomposition", {"b_miss": -380, "b_def": 0, "eta": 5}).json() == {
        "total": "-375", "expected": "-380"}


def test_missing_bias_and_lipschitz_bound():
    effects = {"Fracht": 230, "Produktmix": 150, "Rabatt": 60}
    body = post("/error-budget/missing-bias", {"effects": effects, "observed": ["Rabatt"]}).json()
    assert body == {"b_miss": "-380", "missing": ["Fracht", "Produktmix"]}
    assert post("/error-budget/missing-bias", {"effects": effects, "observed": list(effects)}).json()["b_miss"] == "0"
    assert "nicht in S_q" in _error(post("/error-budget/missing-bias", {"effects": effects, "observed": ["X"]}))
    assert "Exponenten" in _error(post("/error-budget/missing-bias", {"effects": {"a": "1e9999"}, "observed": []}))
    assert post("/error-budget/lipschitz-bound", {"lipschitz": 2, "driver_distance": 10, "b_def": -1,
                                                  "eta": 2}).json() == {"bound": "23"}
    assert "nichtnegativ" in _error(post("/error-budget/lipschitz-bound", {
        "lipschitz": -1, "driver_distance": 1, "b_def": 0, "eta": 0}))


# ----------------------------------------------------------------------------- diagnosis


def test_posterior_increases_h1_when_the_deviation_is_more_likely_under_h1():
    body = post("/diagnosis/posterior", {"prior_h1": "1/5", "likelihood_h1": "3/5", "likelihood_h0": "1/5"}).json()
    assert body == {"odds": "3/4", "probability": "3/7", "increased": True}
    less = post("/diagnosis/posterior", {"prior_h1": "1/5", "likelihood_h1": "1/10", "likelihood_h0": "1/5"}).json()
    assert less["increased"] is False
    assert "undefiniert" in _error(post("/diagnosis/posterior", {"prior_h1": "1/5", "likelihood_h1": 1,
                                                                 "likelihood_h0": 0}))
    assert "Prior" in _error(post("/diagnosis/posterior", {"prior_h1": 1, "likelihood_h1": 1, "likelihood_h0": 1}))


def test_bayes_update_and_voi():
    update = {"prior": {"a": "7/10", "b": "3/10"}, "likelihood": {"a": "1/10", "b": "9/10"}}
    assert post("/diagnosis/bayes-update", update).json() == {"posterior": {"a": "7/34", "b": "27/34"}}
    body = post("/diagnosis/voi", {**update, "gains": {"a": 0, "b": 100}, "cost": 40}).json()
    assert body["expected_gain"] == "1350/17" and body["rational"] is True and body["cost"] == "40"
    assert post("/diagnosis/voi", {**update, "gains": {"a": 0, "b": 100}, "cost": 80}).json()["rational"] is False
    assert "dieselben Zustände" in _error(post("/diagnosis/bayes-update", {
        "prior": {"a": 1}, "likelihood": {"b": 1}}))
    assert "Wahrscheinlichkeit 0" in _error(post("/diagnosis/bayes-update", {
        "prior": {"a": 1}, "likelihood": {"a": 0}}))
    assert "Exponenten" in _error(post("/diagnosis/bayes-update", {"prior": {"a": "1e9999"}, "likelihood": {"a": 1}}))
    assert "nichtnegativ" in _error(post("/diagnosis/voi", {**update, "gains": {"a": 0, "b": 1}, "cost": -1}))


def test_deviation_causes_and_processed_count():
    causes = client.get(url("/diagnosis/causes")).json()["causes"]
    assert [item["name"] for item in causes] == [cause.name for cause in DeviationCause]
    assert causes[0] == {"name": "MISSING_SOURCE", "label": "Fehlende Datenquelle",
                         "response": DeviationCause.MISSING_SOURCE.response}
    body = post("/diagnosis/deviations", {"deviations": [
        {"cause": "MISSING_SOURCE", "outcome": "Frachtdaten angebunden"}, {"cause": "STALE_DATA"},
        {"cause": "UNCLEAR_DEFINITION", "outcome": "   "}]}).json()
    assert (body["total"], body["processed"], body["open"]) == (3, 1, 2)
    assert [item["processed"] for item in body["items"]] == [True, False, False]
    assert body["items"][1]["response"] == DeviationCause.STALE_DATA.response
    assert post("/diagnosis/deviations", {"deviations": []}).json()["total"] == 0
    assert post("/diagnosis/deviations", {"deviations": [{"cause": "ZUFALL"}]}).status_code == 422


# ----------------------------------------------------------------------------- governance


def test_levels_describe_cumulative_requirements():
    levels = client.get(url("/governance/levels")).json()["levels"]
    assert [level["name"] for level in levels] == [level.name for level in ReliabilityLevel]
    assert levels[0]["requirements"] == []
    sizes = [len(level["requirements"]) for level in levels]
    assert sizes == [0, 1, 5, 7]
    assert "Nachweis fehlt: Ein Mensch entscheidet" in levels[2]["requirements"]
    assert "Nachweis fehlt: Ein Mensch entscheidet" not in levels[3]["requirements"]


@pytest.mark.parametrize("level", [1, 2, 3, 4, "HINT", "CROSS_CHECK", "DECISION_PREPARATION", "AUTOMATED_ACTION"])
def test_blockers_match_the_library_for_every_level(level):
    roles = {"data_owner": "A", "use_case_owner": "C"}
    evidence = {"kpis_defined": True, "logging": True}
    body = post("/governance/blockers", {"level": level, "accountabilities": roles, "evidence": evidence}).json()
    parsed = ReliabilityLevel(level) if isinstance(level, int) else ReliabilityLevel[level]
    expected = release_blockers(parsed, Accountabilities(**roles), Evidence(**evidence))
    assert body["blockers"] == expected and body["blocked"] is bool(expected)
    assert body["level"] == parsed.name and body["level_number"] == int(parsed)
    assert "Keine verantwortliche Person benannt: Data Product Owner" in body["blockers"]


def test_blockers_empty_when_everything_is_in_place_and_defaults_block_everything():
    full = {"level": 4, "accountabilities": {"data_owner": "A", "data_product_owner": "B", "use_case_owner": "C"},
            "evidence": {name: True for name in Evidence.__dataclass_fields__}}
    assert post("/governance/blockers", full).json() == {"level": "AUTOMATED_ACTION", "level_number": 4,
                                                         "blocked": False, "blockers": []}
    empty = post("/governance/blockers", {"level": 4}).json()
    assert empty["blocked"] is True and len(empty["blockers"]) == 3 + 1 + 3 + 3
    for bad in (0, 5, "UNBEKANNT", True):
        assert post("/governance/blockers", {"level": bad}).status_code == 422


# ----------------------------------------------------------------------------- integration


def test_integration_selects_the_optimal_sources_and_matches_the_library():
    options = [{"name": "Auftraege", "gain": 0, "cost": 20},
               {"name": "Fracht", "gain": 230, "cost": 80, "requires": ["Auftraege"]},
               {"name": "Produktgruppe", "gain": 150, "cost": 60}]
    body = post("/integration/select", {"options": options, "budget": 120}).json()
    plan = select_integrations([IntegrationOption(o["name"], o["gain"], o["cost"], tuple(o.get("requires", ())))
                                for o in options], 120)
    assert body == {"selected": list(plan.selected), "net_value": plan.net_value, "total_cost": plan.total_cost,
                    "calls": plan.calls}
    assert body["selected"] == ["Auftraege", "Fracht"] and body["net_value"] == 130
    tight = post("/integration/select", {"options": options, "budget": 60}).json()
    assert tight["selected"] == ["Produktgruppe"] and tight["total_cost"] == 60
    unlimited = post("/integration/select", {"options": options}).json()
    assert unlimited["net_value"] == 130 + 90


def test_integration_empty_and_invalid_inputs():
    assert post("/integration/select", {"options": []}).json() == {
        "selected": [], "net_value": 0, "total_cost": 0, "calls": 0}
    assert "eindeutig" in _error(post("/integration/select", {"options": [
        {"name": "A", "gain": 1, "cost": 1}, {"name": "A", "gain": 1, "cost": 1}]}))
    assert "unbekannte Option" in _error(post("/integration/select", {"options": [
        {"name": "A", "gain": 1, "cost": 1, "requires": ["B"]}]}))
    too_many = [{"name": f"S{i}", "gain": 1, "cost": 1} for i in range(web_api.MAX_INTEGRATION_OPTIONS + 1)]
    assert post("/integration/select", {"options": too_many}).status_code == 422
    assert post("/integration/select", {"options": [{"name": "A", "gain": -1, "cost": 1}]}).status_code == 422
    assert post("/integration/select", {"options": [], "budget": -1}).status_code == 422


@pytest.mark.slow
def test_integration_at_the_option_limit_finishes():
    options = [{"name": f"S{i}", "gain": 100 + 97 * i, "cost": 50 + 81 * i % 90,
                "requires": [f"S{(i + 1) % 10}"] if i % 3 == 0 else []}
               for i in range(web_api.MAX_INTEGRATION_OPTIONS)]
    body = post("/integration/select", {"options": options, "budget": 300}).json()
    assert body["total_cost"] <= 300 and body["net_value"] > 0


def test_solver_failure_is_a_503(monkeypatch):
    def broken(*_args, **_kwargs):
        raise BackendError("Entscheider widersprüchlich")

    monkeypatch.setattr(web_api, "select_integrations", broken)
    response = post("/integration/select", {"options": []})
    assert response.status_code == 503
    assert response.json() == {"error": {"type": "backend_error", "message": "Entscheider widersprüchlich"}}


# ----------------------------------------------------------------------------- experiments, case study


def test_fingerprint_matches_the_library_and_is_deterministic():
    body = {"name": "lauf-1", "config": {"epsilon": "1/20"}, "inputs": {"today": "2026-10-22"},
            "versions": {"python": "3.12.0"}}
    first = post("/experiments/fingerprint", body).json()
    record = ExperimentRecord("lauf-1", body["config"], body["inputs"], {}, body["versions"])
    assert first["fingerprint"] == record.fingerprint() and first["record"] == json.loads(record.to_json())
    assert first["versions"] == {"python": "3.12.0"} and first["name"] == "lauf-1"
    assert post("/experiments/fingerprint", body).json() == first
    assert post("/experiments/fingerprint", {**body, "inputs": {"today": "2026-10-23"}}).json()[
        "fingerprint"] != first["fingerprint"]


def test_fingerprint_without_versions_uses_server_versions_and_validates_names():
    body = post("/experiments/fingerprint", {"name": "lauf"}).json()
    assert "python" in body["versions"] and body["record"]["results"] == {}
    for name in ("../x", "", "a/b", ".."):
        assert "einfacher Dateiname" in _error(post("/experiments/fingerprint", {"name": name}))
    assert "Exponenten" in _error(post("/experiments/fingerprint", {"name": "x", "config": {"a": "1e9999"}}))
    assert "Exponenten" in _error(post("/experiments/fingerprint", {"name": "x", "inputs": {"a": ["1e9999"]}}))


def test_versions_endpoint_lists_python_and_dependencies():
    versions = client.get(url("/experiments/versions")).json()["versions"]
    assert set(versions) == {"python", "subgraph-sat-solver-econ"}


def test_case_study_reproduces_the_numbers_of_the_paper():
    body = client.get(url("/case-study")).json()
    case = margin_case()
    assert (body["gap"], body["expected_db2"], body["actual_db2"]) == ("440", "3080", "2640")
    assert [(c["name"], c["amount"]) for c in body["causes"]] == [("Expressfracht", "230"), ("Produktmix", "150"),
                                                                   ("Rabatte", "60")]
    assert sum(Fraction(c["share"]) for c in body["causes"]) == 1
    assert body["explained_share"] == str(case.explained_share) == "3/22"
    assert body["explained_share_percent"] == 13.6
