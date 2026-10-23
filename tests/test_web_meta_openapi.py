"""Meta-Endpunkte, OpenAPI-Dokumentation und Eingabegrenzen der Web-API."""

import tomllib
from pathlib import Path

import pytest

from web import convert
from web.api import API_VERSION, DEFAULT_MAX_BODY_BYTES, app, max_body_bytes, run
from web.schemas import CauseName, LevelName

from aidataeco.diagnosis import DeviationCause
from aidataeco.governance import ReliabilityLevel

from web_helpers import client, post, report_request, url

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parent.parent


def _operations():
    schema = app.openapi()
    return [(method, path, operation) for path, item in schema["paths"].items()
            for method, operation in item.items()]


def test_health_reports_ok():
    assert client.get(url("/health")).json() == {"status": "ok"}


def test_options_list_levels_evidence_causes_directions_and_limits():
    options = client.get(url("/options")).json()
    assert [level["number"] for level in options["levels"]] == [1, 2, 3, 4]
    assert options["levels"][2] == {"number": 3, "name": "DECISION_PREPARATION",
                                    "role": "Vorbereitung von Entscheidungen"}
    assert options["measured_evidence"] == ["kpis_defined", "provenance_available", "quality_measurable",
                                            "error_budget_met"]
    assert options["declared_evidence"] == ["human_decides", "explicit_approval", "logging", "intervention_path"]
    assert "STALE_DATA" in options["deviation_causes"]
    assert options["directions"] == ["IMPROVED", "UNCHANGED", "REGRESSED"]
    assert options["limits"]["max_body_bytes"] == DEFAULT_MAX_BODY_BYTES
    assert options["limits"]["max_exponent_digits"] == convert.MAX_EXPONENT_DIGITS


def test_every_operation_is_documented_with_summary_description_tag_and_response_schema():
    operations = _operations()
    assert len(operations) == 28
    for method, path, operation in operations:
        where = f"{method.upper()} {path}"
        assert operation.get("summary"), where
        assert len(operation.get("description", "")) > 40, where
        assert operation.get("tags"), where
        assert "200" in operation["responses"], where
        if method == "post":
            assert "application/json" in operation["requestBody"]["content"], where
            assert operation["responses"]["422"]["description"], where
            assert operation["responses"]["413"]["description"], where


def test_every_tag_is_declared_and_used():
    schema = app.openapi()
    declared = {tag["name"] for tag in schema["tags"]}
    used = {tag for _, _, operation in _operations() for tag in operation["tags"]}
    assert declared == used


def test_markdown_endpoints_declare_markdown_media_type():
    paths = app.openapi()["paths"]
    for path in ("/api/v1/reports/markdown", "/api/v1/reports/compare/markdown"):
        assert "text/markdown" in paths[path]["post"]["responses"]["200"]["content"]


def test_schema_fields_have_descriptions():
    schemas = app.openapi()["components"]["schemas"]
    undocumented = [f"{name}.{field}" for name, schema in schemas.items()
                    for field, spec in schema.get("properties", {}).items()
                    if not spec.get("description") and "$ref" not in spec and "allOf" not in spec]
    assert undocumented == []


def test_request_models_carry_examples():
    schemas = app.openapi()["components"]["schemas"]
    for name in ("ReportRequest", "PassRateRequest", "BlockersRequest", "IntegrationRequest",
                 "ExplainedShareRequest", "FingerprintRequest"):
        assert schemas[name]["examples"], name


def test_api_version_matches_the_project_version():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert app.version == API_VERSION == pyproject["project"]["version"]


def test_literal_types_follow_the_library_enums():
    assert set(CauseName.__args__) == {cause.name for cause in DeviationCause}
    assert set(LevelName.__args__) == set(ReliabilityLevel.__members__)


def test_docs_pages_are_served():
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").json()["info"]["version"] == API_VERSION


def test_oversized_request_is_rejected_with_413(monkeypatch):
    monkeypatch.setenv("AIDATAECO_API_MAX_BODY_BYTES", "100")
    response = post("/reports", report_request())
    assert response.status_code == 413
    assert response.json()["error"]["type"] == "payload_too_large"
    assert client.get(url("/options")).json()["limits"]["max_body_bytes"] == 100


@pytest.mark.parametrize("value", ["abc", "0", "-5", ""])
def test_invalid_body_limit_falls_back_to_the_default(monkeypatch, value):
    monkeypatch.setenv("AIDATAECO_API_MAX_BODY_BYTES", value)
    assert max_body_bytes() == DEFAULT_MAX_BODY_BYTES
    assert post("/reports", report_request()).status_code == 200


def test_non_numeric_content_length_is_a_400():
    response = client.post(url("/reports"), content=b"{}", headers={"content-length": "abc",
                                                                   "content-type": "application/json"})
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "invalid_header"


def test_run_starts_uvicorn_with_environment_settings(monkeypatch):
    calls = []
    import uvicorn
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.delenv("AIDATAECO_API_HOST", raising=False)
    monkeypatch.delenv("AIDATAECO_API_PORT", raising=False)
    run()
    monkeypatch.setenv("AIDATAECO_API_HOST", "0.0.0.0")
    monkeypatch.setenv("AIDATAECO_API_PORT", "9001")
    run()
    assert calls[0] == (("web.api:app",), {"host": "127.0.0.1", "port": 8000})
    assert calls[1] == (("web.api:app",), {"host": "0.0.0.0", "port": 9001})


@pytest.mark.parametrize("text", ["1e1000", "0.5E+99999", "-1.e-12345", "1e1_000"])
def test_convert_rejects_huge_exponents(text):
    with pytest.raises(ValueError, match="Exponenten"):
        convert.fraction("x", text)
    with pytest.raises(ValueError, match="Exponenten"):
        convert.guard_numbers({"a": [{"b": text}]})


def test_convert_accepts_normal_numbers_and_handles_deep_nesting():
    assert str(convert.fraction("x", "1e100")) == "1" + "0" * 100
    assert convert.optional_fraction("x", None) is None
    assert convert.optional_text(None) is None
    # Hex-Fingerprints und Namen enthalten „e“ und Ziffern, sind aber keine Zahlen.
    convert.guard_numbers(["ed62a191125917f2fadb76daeaa44d3fae69a2bbaf351cd615265981c9dc3bbd", "e123456", "Ae99999"])
    deep = current = []
    for _ in range(5000):
        nxt = []
        current.append(nxt)
        current = nxt
    convert.guard_numbers(deep)
    convert.guard_numbers(("a", 1, {"k": ("b",)}))


@pytest.mark.parametrize("value,expected", [(1, 1), (4, 4), ("HINT", 1), ("AUTOMATED_ACTION", 4)])
def test_convert_level_of(value, expected):
    assert int(convert.level_of(value)) == expected


@pytest.mark.parametrize("value", [0, 5, True, "hint", None, 2.0])
def test_convert_level_of_rejects_invalid_levels(value):
    with pytest.raises(ValueError):
        convert.level_of(value)
