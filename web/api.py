"""Zustandslose JSON-API für aidataeco (Prüfwerkzeug und Bausteine zur Arbeit „Wann ist das Datennetz gut genug für KI?").

Die Endpunkte rufen ausschließlich öffentliche Funktionen aus ``src/`` (Importname ``aidataeco``) auf; es
gibt keine Fachlogik und keinen Zustand auf dem Server. Jede Anfrage enthält ihre Eingaben vollständig.
"""

from __future__ import annotations

import json
import os
from fractions import Fraction
from typing import Any, Dict, List, Mapping, Optional, Sequence

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from aidataeco.compare import compare_reports
from aidataeco.casestudy import margin_case
from aidataeco.diagnosis import (Deviation, DeviationCause, bayes_update, expected_gain, integration_rational,
                                 posterior_odds, posterior_probability, processed_deviations)
from aidataeco.errorbudget import (ErrorBudget, ErrorDecomposition, good_enough_linear, is_good_enough,
                                   linear_loss, lipschitz_bound, missing_bias)
from aidataeco.evaluation import (Cause, ReferenceCase, attribute_completeness, evaluate, explained_share,
                                  is_fresh)
from aidataeco.experiment import ExperimentRecord, collect_versions
from aidataeco.governance import Accountabilities, Evidence, ReliabilityLevel, release_blockers
from aidataeco.integration import IntegrationOption, select_integrations
from aidataeco.model import Answer, Provenance
from aidataeco.parsing import as_date, as_text
from aidataeco.provider import StaticProvider, collect_answers
from aidataeco.report import GoLiveReport, build_report
from aidataeco.spec import MEASURED, ORGANIZATIONAL, Spec, answers_for, parse_answers, parse_spec
from subgraph_sat_solver_econ.backends import BackendError

from . import convert
from .convert import fraction, fractions_of, guard_numbers, optional_fraction, optional_text, text
from .schemas import (MAX_INTEGRATION_OPTIONS, MAX_INTEGRATION_VALUE, BayesUpdateRequest, BayesUpdateResponse,
                      BlockersRequest, BlockersResponse, BudgetCheckRequest, BudgetCheckResponse, CasesRequest,
                      CasesResponse, CaseResult, CaseStudyCause, CaseStudyResponse, CompletenessRequest,
                      CompletenessResponse, ComparisonResponse, DecompositionRequest, DecompositionResponse,
                      DeviationCauseModel, DeviationCausesResponse, DeviationItem, DeviationsRequest,
                      DeviationsResponse, ErrorResponse, EvaluationModel, ExplainedShareRequest,
                      ExplainedShareResponse, FingerprintRequest, FingerprintResponse, FreshnessRequest,
                      FreshnessResponse, HealthResponse, IntegrationRequest, IntegrationResponse, LevelDescription,
                      LevelOption, LevelsResponse, LimitsResponse, LinearLossRequest, LinearLossResponse,
                      LipschitzRequest, LipschitzResponse, MissingBiasRequest, MissingBiasResponse,
                      OptionsResponse, PassRateRequest, PassRateResponse, PosteriorRequest, PosteriorResponse,
                      ReportCompareRequest, ReportRequest, ReportResponse, SpecRequest, SpecSummary,
                      SpecValidationResponse, ValidationErrorResponse, VersionsResponse, VoiRequest, VoiResponse)

API_PREFIX = "/api/v1"
API_VERSION = "3.0.0"
#: Standardgrenze für die Request-Größe; überschreibbar über ``AIDATAECO_API_MAX_BODY_BYTES``.
DEFAULT_MAX_BODY_BYTES = 1_048_576

app = FastAPI(
    title="aidataeco API",
    summary="Freigabebericht, Error Budget und Diagnose für KI auf dem Datennetz als JSON API",
    description="""
    Die **aidataeco API** stellt die Bausteine der Arbeit „Wann ist das Datennetz gut genug für KI?“ als
    zustandslose JSON-Endpunkte bereit. Jede Anfrage enthält ihre Eingaben vollständig; es gibt keine
    Sitzung und keine serverseitige Speicherung. Alle Rechnungen sind exakt (Brüche), ohne Zufall und ohne
    Zugriff auf die Systemuhr: Der Stichtag ist immer eine Eingabe.

    ## Ablauf der Freigabeprüfung

    1. Eine Spezifikation mit `POST /api/v1/specs/validate` prüfen (Datennetz, Data Product, Verantwortliche,
       Anwendungsfall mit Stufe, Error Budget und Referenzfragen).
    2. Die Antworten der KI auf die Referenzfragen mit `POST /api/v1/reports/cases` ansehen.
    3. Den **Freigabebericht** mit `POST /api/v1/reports` berechnen (Stichtag und erwarteter Verlust sind Eingabe);
       `.../reports/markdown` liefert dieselbe Auswertung als lesbaren Text.
    4. Spätere Berichte mit `POST /api/v1/reports/compare` gegen frühere vergleichen: Der Vergleich meldet eine
       **Regression**, wenn sich eine Kennzahl verschlechtert oder ein Freigabehindernis neu hinzukommt.

    ## Weitere Bausteine

    Die Endpunkte unter `evaluation`, `error-budget`, `diagnosis`, `governance`, `integration`, `experiments` und
    `case-study` machen einzelne Rechenschritte der Arbeit einzeln zugänglich: Bestehensquote und erklärter Anteil,
    Gut-genug-Bedingung und Fehlerzerlegung, Bayes-Indikator und VOI-Bedingung, Freigabehindernisse je
    Vertrauensstufe, Auswahl von Datenquellen unter Budget sowie die Fallstudie „Warum sinkt die Marge?“.

    ## Zahlen, Eingaben und Fehler

    Zahlen sind JSON-Zahlen oder Texte (`"3/20"`, `"0.15"`); Ergebnisse stehen als Bruch-Text. Spezifikationen,
    Antworten und Berichte verwenden dieselben Schlüssel wie die Dateien der Kommandozeile und werden streng
    gelesen: Unbekannte Felder, falsche Typen und ungültige Zahlen werden abgewiesen. Fachliche Eingabefehler
    antworten mit HTTP **422** und dem Schema `{"error":{"type":"input_error","message":"..."}}`; ungültige
    JSON-Feldtypen weist FastAPI ebenfalls mit HTTP 422 ab (Schema `detail`). Zu große Anfragen (`Content-Length`
    über der Grenze aus `GET /api/v1/options`) beantwortet die API mit HTTP **413**.

    ## Aussagekraft

    Ein Freigabebericht **ohne** Freigabehindernisse ist keine Freigabe, sondern nur die Feststellung, dass keine
    der formalisierten Bedingungen verletzt ist. Organisatorische Nachweise werden erklärt, nicht überprüft; die
    Freigabe verantwortet der Use-Case Owner. Die Vertrauensstufen sind ein konzeptioneller Rahmen und keine Norm.
    """,
    version=API_VERSION,
    openapi_tags=[
        {"name": "meta", "description": "Status, zulässige Optionen und Eingabegrenzen."},
        {"name": "specs", "description": "Spezifikationen von Data Product und Anwendungsfall prüfen."},
        {"name": "reports", "description": "Freigabebericht berechnen, Antworten auswerten und Berichte über die Zeit vergleichen."},
        {"name": "evaluation", "description": "Kennzahlen zu Reife und Nutzen: Bestehensquote, erklärter Anteil, Vollständigkeit, Aktualität."},
        {"name": "error-budget", "description": "Gut-genug-Bedingung, Fehlerzerlegung und Schranken."},
        {"name": "diagnosis", "description": "Abweichungen als diagnostisches Signal: Bayes-Indikator, Lern-Loop, VOI-Bedingung."},
        {"name": "governance", "description": "Vertrauensstufen, Verantwortlichkeiten und Freigabehindernisse."},
        {"name": "integration", "description": "Auswahl von Datenquellen unter Budget und Abhängigkeiten."},
        {"name": "experiments", "description": "Reproduzierbares Experimentprotokoll und Versionen."},
        {"name": "case-study", "description": "Illustrative Fallstudie „Warum sinkt die Marge?“."},
    ],
)


class MarkdownResponse(Response):
    """Antwort mit Markdown-Text (``text/markdown; charset=utf-8``)."""

    media_type = "text/markdown"


_MARKDOWN_OK = {200: {"description": "Lesbare Markdown-Fassung der Auswertung.",
                      "content": {"text/markdown": {"schema": {"type": "string"}}}}}

INPUT_ERRORS = {
    422: {
        "model": ErrorResponse | ValidationErrorResponse,
        "description": "Ungültige Eingabe: fachlicher Fehler (Schema `error`) oder ungültiges Request-Feld (Schema `detail`).",
        "content": {"application/json": {"examples": {
            "input_error": {"summary": "Fachlicher Eingabefehler",
                            "value": {"error": {"type": "input_error", "message": "Spezifikation: Pflichtfeld fehlt: network"}}},
            "request_validation": {"summary": "Fehlerhafte Request-Validierung",
                                   "value": {"detail": [{"loc": ["body", "today"], "msg": "Field required", "type": "missing"}]}},
        }}},
    },
    413: {"model": ErrorResponse, "description": "Die Anfrage überschreitet die zulässige Größe (`Content-Length`)."},
}


# --------------------------------------------------------------------------------------------------
# Fehlerbehandlung und Eingabegrenzen
# --------------------------------------------------------------------------------------------------


def _error(status: int, kind: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"type": kind, "message": message}})


def max_body_bytes() -> int:
    """Größte zulässige Request-Größe; ``AIDATAECO_API_MAX_BODY_BYTES`` überschreibt den Standard.

    Ein ungültiger oder nicht positiver Wert der Umgebungsvariablen wird ignoriert.
    """
    try:
        value = int(os.environ["AIDATAECO_API_MAX_BODY_BYTES"])
    except (KeyError, ValueError):
        return DEFAULT_MAX_BODY_BYTES
    return value if value > 0 else DEFAULT_MAX_BODY_BYTES


@app.exception_handler(ValueError)
async def input_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    """Die Bibliothek meldet ungültige Eingaben ausnahmslos als ``ValueError``; das ist ein 422."""
    return _error(422, "input_error", str(exc))


@app.exception_handler(BackendError)
async def backend_error_handler(_: Request, exc: BackendError) -> JSONResponse:
    """Der Entscheider des Solvers konnte keine verlässliche Antwort liefern."""
    return _error(503, "backend_error", str(exc))


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Weist Anfragen ab, deren ``Content-Length`` die Grenze überschreitet (Schutz vor übergroßen Dokumenten).

    Chunked-Übertragungen ohne ``Content-Length`` prüft diese Schicht nicht; dafür ist der vorgeschaltete
    Reverse Proxy zuständig.
    """
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            size = int(declared)
        except ValueError:
            return _error(400, "invalid_header", "Content-Length ist keine ganze Zahl")
        if size > max_body_bytes():
            return _error(413, "payload_too_large", f"Anfrage größer als {max_body_bytes()} Bytes")
    return await call_next(request)


# --------------------------------------------------------------------------------------------------
# Hilfsfunktionen: Eingaben lesen, Ergebnisse serialisieren
# --------------------------------------------------------------------------------------------------


def _spec(mapping: Mapping[str, Any]) -> Spec:
    guard_numbers(mapping, "spec")
    return parse_spec(mapping)


def _answers(spec: Spec, mapping: Mapping[str, Any]) -> Sequence[Answer]:
    guard_numbers(mapping, "answers")
    return answers_for(spec, mapping)


def _report_of(request: ReportRequest) -> GoLiveReport:
    spec = _spec(request.spec)
    answers = _answers(spec, request.answers)
    return build_report(spec, answers, as_date("today", request.today),
                        optional_fraction("expected_loss", request.expected_loss), request.versions)


def _evaluation_payload(evaluation: Any) -> Optional[EvaluationModel]:
    if evaluation is None:
        return None
    return EvaluationModel(pass_rate=text(evaluation.pass_rate),
                           provenance_coverage=text(evaluation.provenance_coverage),
                           unanswered=evaluation.unanswered)


def _case_results(cases: Sequence[ReferenceCase], answers: Sequence[Answer]) -> List[CaseResult]:
    results = []
    for case, answer in zip(cases, answers):
        provenance = answer.provenance if answer.provenance is not None else Provenance()
        results.append(CaseResult(
            question=case.question, reference=text(case.reference), tolerance=text(case.tolerance),
            weight=text(case.weight), value=optional_text(answer.value), answered=answer.value is not None,
            passed=case.passed(answer), provenance_complete=provenance.is_complete(),
            provenance_missing=list(provenance.missing())))
    return results


def _level_options() -> List[LevelOption]:
    return [LevelOption(number=int(level), name=level.name, role=convert.LEVEL_ROLES[level])
            for level in ReliabilityLevel]


def _level_requirements(level: ReliabilityLevel) -> List[str]:
    """Anforderungen einer Stufe: die Hindernisse bei vollständiger Besetzung, aber ohne jeden Nachweis."""
    return release_blockers(level, Accountabilities("-", "-", "-"), Evidence())


def _budget(stakes: object, epsilon: object) -> ErrorBudget:
    return ErrorBudget(fraction("stakes", stakes), fraction("epsilon", epsilon))


def _deviation_items(items: Sequence[Deviation]) -> List[DeviationItem]:
    return [DeviationItem(cause=item.cause.name, label=item.cause.value, response=item.cause.response,
                          processed=item.processed) for item in items]


# --------------------------------------------------------------------------------------------------
# meta
# --------------------------------------------------------------------------------------------------


@app.get(
    f"{API_PREFIX}/health",
    tags=["meta"],
    summary="API-Erreichbarkeit prüfen",
    description="Liefert einen einfachen Prozessstatus. Der Endpunkt führt keine Probe der Abhängigkeiten aus.",
    response_model=HealthResponse,
)
def health() -> Dict[str, str]:
    """Gibt `ok` zurück, wenn der API-Prozess Anfragen entgegennehmen kann."""
    return {"status": "ok"}


@app.get(
    f"{API_PREFIX}/options",
    tags=["meta"],
    summary="Zulässige Optionen und Grenzen abrufen",
    description="Gibt die Vertrauensstufen, die messbaren und erklärbaren Nachweise, die Abweichungsursachen, die "
                "Richtungen des Berichtsvergleichs und die Eingabegrenzen der API zurück. Die Werte eignen sich zum "
                "Aufbau von Client-Auswahllisten.",
    response_model=OptionsResponse,
)
def options() -> Dict[str, Any]:
    """Liefert die von Spezifikation und Endpunkten akzeptierten Auswahlwerte."""
    from aidataeco.compare import Direction
    return {
        "levels": _level_options(),
        "measured_evidence": list(MEASURED),
        "declared_evidence": list(ORGANIZATIONAL),
        "deviation_causes": [cause.name for cause in DeviationCause],
        "directions": [direction.name for direction in Direction],
        "limits": LimitsResponse(
            max_body_bytes=max_body_bytes(), max_integration_options=MAX_INTEGRATION_OPTIONS,
            max_integration_value=MAX_INTEGRATION_VALUE, max_exponent_digits=convert.MAX_EXPONENT_DIGITS),
    }


# --------------------------------------------------------------------------------------------------
# specs
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/specs/validate",
    tags=["specs"],
    summary="Spezifikation prüfen",
    description="Liest die Spezifikation streng und fasst sie zusammen. Eine gültige Spezifikation antwortet mit "
                "`valid: true`; jede Abweichung (unbekannte Felder, falsche Typen, nicht benannte Knoten, doppelte "
                "Referenzfragen, erklärte messbare Nachweise …) antwortet mit HTTP 422. Die Prüfung bewertet nicht, "
                "ob der Anwendungsfall freigabereif ist; dafür dient `POST /api/v1/reports`.",
    response_model=SpecValidationResponse,
    responses=INPUT_ERRORS,
)
def validate_spec(request: SpecRequest) -> Dict[str, Any]:
    """Prüft die Spezifikation und gibt eine Zusammenfassung zurück."""
    spec = _spec(request.spec)
    use_case = spec.use_case
    summary = SpecSummary(
        product=spec.product.name, version=spec.product.label.version, owner=spec.product.label.owner,
        level=use_case.level.name, level_number=int(use_case.level),
        nodes=sorted(spec.product.node_names), required_links=[list(link) for link in spec.required_links],
        kpis=list(spec.kpis), reference_cases=len(use_case.cases),
        error_budget_limit=None if use_case.budget is None else text(use_case.budget.limit),
        min_pass_rate=optional_text(use_case.min_pass_rate),
        missing_accountabilities=list(spec.accountabilities.missing()),
        declared_evidence={name: getattr(spec.declared, name) for name in ORGANIZATIONAL})
    return {"valid": True, "summary": summary}


# --------------------------------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/reports",
    tags=["reports"],
    summary="Freigabebericht berechnen",
    description="Prüft Spezifikation und Antworten zum Stichtag und liefert den Freigabebericht. Kennzahlen, "
                "Provenance, Qualität und Error Budget werden aus den Eingaben abgeleitet; fehlender Nachweis zählt "
                "nie als erfüllt. `blockers` nennt, was einer Freigabe auf der angestrebten Stufe im Weg steht; "
                "`blocked: false` ist keine Freigabe. Der `fingerprint` bindet Eingaben und Versionen; mit "
                "angegebenen `versions` ist der Bericht reproduzierbar. Die Antwort entspricht dem JSON der "
                "Kommandozeile (`aidataeco report --format json`).",
    response_model=ReportResponse,
    responses=INPUT_ERRORS,
)
def create_report(request: ReportRequest) -> Dict[str, Any]:
    """Berechnet den Freigabebericht und gibt ihn im JSON-Format der Kommandozeile zurück."""
    return _report_of(request).to_dict()


@app.post(
    f"{API_PREFIX}/reports/markdown",
    tags=["reports"],
    summary="Freigabebericht als Markdown ausgeben",
    description="Berechnet denselben Bericht wie `POST /api/v1/reports` und gibt ihn als lesbaren Markdown-Text "
                "zurück (Kennzahlen, Nachweise, Knoten, offene Verknüpfungen, Versionen).",
    response_class=MarkdownResponse,
    responses={**_MARKDOWN_OK, **INPUT_ERRORS},
)
def create_report_markdown(request: ReportRequest) -> Response:
    """Gibt die Markdown-Fassung des Freigabeberichts zurück."""
    return MarkdownResponse(_report_of(request).to_markdown())


@app.post(
    f"{API_PREFIX}/reports/cases",
    tags=["reports"],
    summary="Antworten je Referenzfrage auswerten",
    description="Wertet die Antworten der KI gegen die Referenzfragen der Spezifikation aus: je Frage Antwort, "
                "Bestehen innerhalb der Toleranz und Vollständigkeit der Provenance, dazu die aggregierten Kennzahlen. "
                "Eine fehlende Antwort besteht nie. Der Endpunkt berechnet keine Freigabehindernisse.",
    response_model=CasesResponse,
    responses=INPUT_ERRORS,
)
def evaluate_cases(request: CasesRequest) -> Dict[str, Any]:
    """Wertet jede Referenzfrage einzeln aus und fasst die Kennzahlen zusammen."""
    spec = _spec(request.spec)
    cases = spec.use_case.cases
    answers = _answers(spec, request.answers)
    return {"cases": _case_results(cases, answers),
            "evaluation": _evaluation_payload(evaluate(cases, answers) if cases else None)}


@app.post(
    f"{API_PREFIX}/reports/compare",
    tags=["reports"],
    summary="Zwei Freigabeberichte vergleichen",
    description="Vergleicht einen früheren mit einem späteren Bericht desselben Data Products exakt, ohne Rundung "
                "oder Toleranz. Fehlender Nachweis ist stets schlechter als jeder belegte Wert. Eine **Regression** "
                "liegt vor, wenn sich mindestens eine der sieben Kennzahlen verschlechtert oder ein Freigabehindernis "
                "neu hinzukommt (`has_regression`). `fingerprint_changed` zeigt, ob sich die Eingaben geändert haben; "
                "eine Änderung des Datennetzes lässt sich von einer Änderung des Testsatzes nicht trennen.",
    response_model=ComparisonResponse,
    responses=INPUT_ERRORS,
)
def compare(request: ReportCompareRequest) -> Dict[str, Any]:
    """Vergleicht zwei gespeicherte Berichte."""
    return _comparison(request).to_dict()


@app.post(
    f"{API_PREFIX}/reports/compare/markdown",
    tags=["reports"],
    summary="Berichtsvergleich als Markdown ausgeben",
    description="Berechnet denselben Vergleich wie `POST /api/v1/reports/compare` und gibt ihn als Markdown-Tabelle zurück.",
    response_class=MarkdownResponse,
    responses={**_MARKDOWN_OK, **INPUT_ERRORS},
)
def compare_markdown(request: ReportCompareRequest) -> Response:
    """Gibt die Markdown-Fassung des Vergleichs zurück."""
    return MarkdownResponse(_comparison(request).to_markdown())


def _comparison(request: ReportCompareRequest):
    guard_numbers(request.old, "old")
    guard_numbers(request.new, "new")
    return compare_reports(GoLiveReport.from_dict(request.old), GoLiveReport.from_dict(request.new))


# --------------------------------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/evaluation/pass-rate",
    tags=["evaluation"],
    summary="Bestehensquote und Provenance-Abdeckung berechnen",
    description="Berechnet die gewichtete Bestehensquote `Σ w·1[|ŷ − y*| ≤ δ] / Σ w`, die Provenance-Abdeckung und die "
                "Zahl unbeantworteter Fragen aus Referenzfragen und Antworten. Die Kennzahlen stehen getrennt, nie als "
                "Gesamtnote. Fragen ohne Antwort gelten als nicht bestanden und ohne Provenance.",
    response_model=PassRateResponse,
    responses=INPUT_ERRORS,
)
def pass_rate(request: PassRateRequest) -> Dict[str, Any]:
    """Wertet Antworten gegen Referenzfragen aus."""
    cases = tuple(ReferenceCase(item.question, fraction("reference", item.reference),
                                fraction("tolerance", item.tolerance), fraction("weight", item.weight))
                  for item in request.cases)
    questions = [case.question for case in cases]
    if len(set(questions)) != len(questions):
        raise ValueError("Fragen der Referenzfälle müssen eindeutig sein")
    mapping = {question: answer.model_dump(mode="json") for question, answer in request.answers.items()}
    guard_numbers(mapping, "answers")
    parsed = parse_answers(mapping)
    unknown = sorted(set(parsed) - set(questions))
    if unknown:
        raise ValueError(f"Antworten zu unbekannten Fragen: {', '.join(unknown)}")
    answers = collect_answers(cases, StaticProvider(parsed))
    return {"cases": _case_results(cases, answers), "evaluation": _evaluation_payload(evaluate(cases, answers))}


@app.post(
    f"{API_PREFIX}/evaluation/explained-share",
    tags=["evaluation"],
    summary="Erklärten Anteil am Gesamteffekt berechnen",
    description="Berechnet den von der KI erklärten Anteil eines bekannten Effekts: `1 − g` mit der Rechenlücke "
                "`g = (opt − A)/opt`, wobei `opt` der Gesamteffekt und `A = Σ Betrag·erklärter Anteil` ist. Ohne "
                "`total_effect` ist der Gesamteffekt die Summe der Beträge; ein größerer Wert lässt einen nicht "
                "zugeordneten Rest unerklärt. Ein Gesamteffekt von 0 oder unterhalb der erklärten Summe ist ein Fehler.",
    response_model=ExplainedShareResponse,
    responses=INPUT_ERRORS,
)
def explained_share_of(request: ExplainedShareRequest) -> Dict[str, str]:
    """Berechnet erklärten und unerklärten Anteil."""
    causes = [Cause(item.name, fraction("amount", item.amount), fraction("explained", item.explained))
              for item in request.causes]
    total = optional_fraction("total_effect", request.total_effect)
    share = explained_share(causes, total)
    effect = sum((cause.amount for cause in causes), Fraction(0)) if total is None else total
    return {"explained_share": text(share), "unexplained_share": text(1 - share),
            "explained_amount": text(sum((cause.amount * cause.explained for cause in causes), Fraction(0))),
            "total_effect": text(effect)}


@app.post(
    f"{API_PREFIX}/evaluation/completeness",
    tags=["evaluation"],
    summary="Vollständigkeit eines kritischen Attributs messen",
    description="Berechnet den Belegungsgrad eines Attributs über die übergebenen Zeilen. `null`, fehlende Schlüssel "
                "und leere Texte gelten als nicht belegt. Ohne Zeilen antwortet die API mit HTTP 422.",
    response_model=CompletenessResponse,
    responses=INPUT_ERRORS,
)
def completeness(request: CompletenessRequest) -> Dict[str, Any]:
    """Misst, wie vollständig ein Attribut belegt ist."""
    value = attribute_completeness(request.rows, request.attribute)
    rows = len(request.rows)
    return {"completeness": text(value), "rows": rows, "filled": int(value * rows)}


@app.post(
    f"{API_PREFIX}/evaluation/freshness",
    tags=["evaluation"],
    summary="Aktualität prüfen",
    description="Prüft, ob die letzte Aktualisierung höchstens `frequency_days` Tage vor dem Stichtag liegt. Eine "
                "unbekannte (`null`) oder in der Zukunft liegende Aktualisierung gilt als nicht aktuell.",
    response_model=FreshnessResponse,
    responses=INPUT_ERRORS,
)
def freshness(request: FreshnessRequest) -> Dict[str, Any]:
    """Prüft die Aktualität eines Knotens zum Stichtag."""
    today = as_date("today", request.today)
    updated = None if request.updated is None else as_date("updated", request.updated)
    return {"fresh": is_fresh(updated, request.frequency_days, today),
            "age_days": None if updated is None else (today - updated).days}


# --------------------------------------------------------------------------------------------------
# error-budget
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/error-budget/check",
    tags=["error-budget"],
    summary="Gut-genug-Bedingung prüfen",
    description="Prüft die ökonomische Gut-genug-Bedingung `E[L(ŷ, y*)] ≤ ε·W`. Die Arbeit setzt keinen universellen "
                "Schwellenwert: Stakes `W` und Anteil `ε` müssen für den Anwendungsfall fachlich bestimmt werden.",
    response_model=BudgetCheckResponse,
    responses=INPUT_ERRORS,
)
def check_budget(request: BudgetCheckRequest) -> Dict[str, Any]:
    """Vergleicht den erwarteten Verlust mit dem Error Budget."""
    budget = _budget(request.stakes, request.epsilon)
    loss = fraction("expected_loss", request.expected_loss)
    return {"limit": text(budget.limit), "expected_loss": text(loss),
            "good_enough": is_good_enough(loss, budget), "headroom": text(budget.limit - loss)}


@app.post(
    f"{API_PREFIX}/error-budget/linear-loss",
    tags=["error-budget"],
    summary="Gut-genug-Bedingung unter linearem Loss prüfen",
    description="Berechnet den erwarteten Verlust `c·E|B_miss + B_def + η|` und prüft ihn gegen `ε·W`.",
    response_model=LinearLossResponse,
    responses=INPUT_ERRORS,
)
def check_linear_loss(request: LinearLossRequest) -> Dict[str, Any]:
    """Prüft die praktische Bedingung unter linearem Loss."""
    budget = _budget(request.stakes, request.epsilon)
    cost = fraction("cost_per_unit", request.cost_per_unit)
    error = fraction("expected_abs_error", request.expected_abs_error)
    return {"expected_loss": text(linear_loss(cost, error)), "limit": text(budget.limit),
            "good_enough": good_enough_linear(cost, error, budget)}


@app.post(
    f"{API_PREFIX}/error-budget/decomposition",
    tags=["error-budget"],
    summary="Fehlerzerlegung berechnen",
    description="Fasst den Antwortfehler `ŷ − y* = B_miss + B_def + η` zusammen. Der Erwartungswert ist "
                "`B_miss + B_def`, weil das Rauschen `η` Erwartungswert 0 hat.",
    response_model=DecompositionResponse,
    responses=INPUT_ERRORS,
)
def decomposition(request: DecompositionRequest) -> Dict[str, str]:
    """Berechnet Gesamtfehler und Erwartungswert aus den drei Bestandteilen."""
    parts = ErrorDecomposition(fraction("b_miss", request.b_miss), fraction("b_def", request.b_def),
                               fraction("eta", request.eta))
    return {"total": text(parts.total), "expected": text(parts.expected)}


@app.post(
    f"{API_PREFIX}/error-budget/missing-bias",
    tags=["error-budget"],
    summary="Bias durch fehlende Einflussgrößen berechnen",
    description="Berechnet `B_miss = −Σ α_i·s_i` über alle wesentlichen Einflussgrößen, die im Datennetz nicht "
                "beobachtbar sind. Beobachtete Größen, die nicht zu den wesentlichen gehören, sind ein Fehler.",
    response_model=MissingBiasResponse,
    responses=INPUT_ERRORS,
)
def missing_bias_of(request: MissingBiasRequest) -> Dict[str, Any]:
    """Summiert die Beiträge der nicht beobachteten Einflussgrößen."""
    effects = fractions_of("effects", request.effects)
    bias = missing_bias(effects, request.observed)
    return {"b_miss": text(bias), "missing": sorted(set(effects) - set(request.observed))}


@app.post(
    f"{API_PREFIX}/error-budget/lipschitz-bound",
    tags=["error-budget"],
    summary="Fehlerschranke im nichtlinearen Modell berechnen",
    description="Berechnet die Schranke `|ŷ − y*| ≤ L·‖S_q − S̃_q‖ + |B_def| + |η|` der nichtlinearen Erweiterung.",
    response_model=LipschitzResponse,
    responses=INPUT_ERRORS,
)
def lipschitz(request: LipschitzRequest) -> Dict[str, str]:
    """Berechnet die Lipschitz-Schranke für den Antwortfehler."""
    bound = lipschitz_bound(fraction("lipschitz", request.lipschitz),
                            fraction("driver_distance", request.driver_distance),
                            fraction("b_def", request.b_def), fraction("eta", request.eta))
    return {"bound": text(bound)}


# --------------------------------------------------------------------------------------------------
# diagnosis
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/diagnosis/posterior",
    tags=["diagnosis"],
    summary="Abweichung als Bayes-Indikator auswerten",
    description="Berechnet aus Prior `P(H1)` und Likelihoods `p(d|H1)`, `p(d|H0)` die Posterior Odds und die "
                "Wahrscheinlichkeit von `H1` („es fehlt ein Treiber oder es gibt einen Definitionskonflikt“). Das ist ein "
                "diagnostischer Hinweis, kein Beweis. Eine Likelihood `p(d|H0) = 0` ist undefiniert und ein Fehler.",
    response_model=PosteriorResponse,
    responses=INPUT_ERRORS,
)
def posterior(request: PosteriorRequest) -> Dict[str, Any]:
    """Berechnet Odds und Posterior für `H1`."""
    prior = fraction("prior_h1", request.prior_h1)
    l1 = fraction("likelihood_h1", request.likelihood_h1)
    l0 = fraction("likelihood_h0", request.likelihood_h0)
    probability = posterior_probability(prior, l1, l0)
    return {"odds": text(posterior_odds(prior, l1, l0)), "probability": text(probability),
            "increased": probability > prior}


@app.post(
    f"{API_PREFIX}/diagnosis/bayes-update",
    tags=["diagnosis"],
    summary="Lern-Loop: Posterior über Netzzustände berechnen",
    description="Berechnet `π₁(θ) ∝ p(d|θ)·π₀(θ)` über einem endlichen Zustandsraum. Prior und Likelihood müssen "
                "dieselben Zustände haben; der Prior summiert sich zu 1. Eine Beobachtung mit Wahrscheinlichkeit 0 unter "
                "dem Prior ist ein Fehler.",
    response_model=BayesUpdateResponse,
    responses=INPUT_ERRORS,
)
def bayes(request: BayesUpdateRequest) -> Dict[str, Any]:
    """Aktualisiert die Einschätzung des Datennetzes nach einer Abweichung."""
    result = bayes_update(fractions_of("prior", request.prior), fractions_of("likelihood", request.likelihood))
    return {"posterior": {state: text(value) for state, value in result.items()}}


@app.post(
    f"{API_PREFIX}/diagnosis/voi",
    tags=["diagnosis"],
    summary="VOI-Bedingung für eine Datenerweiterung prüfen",
    description="Berechnet den Posterior, den erwarteten Zusatznutzen `E[ΔW] = Σ π₁(θ)·ΔW(θ)` und prüft die "
                "VOI-Bedingung `E[ΔW] ≥ C_int`. Das ist ein Entscheidungsrahmen; belastbar wird er erst mit "
                "konkreten Annahmen zu Kosten, Nutzen und Unsicherheit.",
    response_model=VoiResponse,
    responses=INPUT_ERRORS,
)
def voi(request: VoiRequest) -> Dict[str, Any]:
    """Entscheidet, ob eine zusätzliche Datenquelle ihre Integrationskosten rechtfertigt."""
    result = bayes_update(fractions_of("prior", request.prior), fractions_of("likelihood", request.likelihood))
    gain = expected_gain(result, fractions_of("gains", request.gains))
    cost = fraction("cost", request.cost)
    return {"posterior": {state: text(value) for state, value in result.items()},
            "expected_gain": text(gain), "cost": text(cost), "rational": integration_rational(gain, cost)}


@app.get(
    f"{API_PREFIX}/diagnosis/causes",
    tags=["diagnosis"],
    summary="Mögliche Abweichungsursachen und Reaktionen abrufen",
    description="Gibt die fünf Ursachen einer Abweichung zwischen KI-Antwort und interner Analyse mit der jeweils "
                "geeigneten Reaktion zurück (Tabelle „Mögliche Ursachen einer Abweichung“ der Arbeit).",
    response_model=DeviationCausesResponse,
)
def deviation_causes() -> Dict[str, Any]:
    """Listet die Ursachen mit Bezeichnung und Reaktion."""
    return {"causes": [DeviationCauseModel(name=cause.name, label=cause.value, response=cause.response)
                       for cause in DeviationCause]}


@app.post(
    f"{API_PREFIX}/diagnosis/deviations",
    tags=["diagnosis"],
    summary="Bearbeitete Abweichungen zählen",
    description="Berechnet die Kennzahl „Bearbeitete Abweichungen“: Eine Abweichung gilt als bearbeitet, wenn eine "
                "dokumentierte Korrektur oder eine begründete Bestätigung vorliegt (`outcome` nicht leer). Die Antwort "
                "enthält zu jeder Abweichung die geeignete Reaktion.",
    response_model=DeviationsResponse,
    responses=INPUT_ERRORS,
)
def deviations(request: DeviationsRequest) -> Dict[str, Any]:
    """Zählt bearbeitete und offene Abweichungen."""
    items = [Deviation(DeviationCause[item.cause], item.outcome) for item in request.deviations]
    done = processed_deviations(items)
    return {"total": len(items), "processed": done, "open": len(items) - done, "items": _deviation_items(items)}


# --------------------------------------------------------------------------------------------------
# governance
# --------------------------------------------------------------------------------------------------


@app.get(
    f"{API_PREFIX}/governance/levels",
    tags=["governance"],
    summary="Vertrauensstufen und ihre Anforderungen abrufen",
    description="Beschreibt die vier Nutzungsstufen (Hinweis, Gegenprüfung, Vorbereitung von Entscheidungen, "
                "Automatisierte Handlung) und die Nachweise, die jede Stufe verlangt (einschließlich der niedrigeren). "
                "Verantwortliche sind auf jeder Stufe Pflicht. Die Stufen sind ein konzeptioneller Rahmen und keine Norm.",
    response_model=LevelsResponse,
)
def levels() -> Dict[str, Any]:
    """Listet die Stufen mit ihren Anforderungen."""
    return {"levels": [LevelDescription(number=option.number, name=option.name, role=option.role,
                                        requirements=_level_requirements(ReliabilityLevel(option.number)))
                       for option in _level_options()]}


@app.post(
    f"{API_PREFIX}/governance/blockers",
    tags=["governance"],
    summary="Freigabehindernisse für eine Stufe bestimmen",
    description="Bestimmt aus Stufe, benannten Verantwortlichen und vorliegenden Nachweisen die Gründe, die eine "
                "Freigabe verhindern. Fehlende Verantwortliche blockieren jede Stufe; auf Stufe 3 muss zusätzlich ein "
                "Mensch entscheiden, auf Stufe 4 sind stattdessen Freigabe, Protokollierung und Eingriffspfad nötig. "
                "Eine leere Liste ist keine Freigabe.",
    response_model=BlockersResponse,
    responses=INPUT_ERRORS,
)
def blockers(request: BlockersRequest) -> Dict[str, Any]:
    """Bestimmt die Freigabehindernisse einer Stufe."""
    level = convert.level_of(request.level)
    found = release_blockers(level, convert.accountabilities_of(request.accountabilities.model_dump()),
                             convert.evidence_of(request.evidence.model_dump()))
    return {"level": level.name, "level_number": int(level), "blocked": bool(found), "blockers": found}


# --------------------------------------------------------------------------------------------------
# integration
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/integration/select",
    tags=["integration"],
    summary="Datenquellen unter Budget und Abhängigkeiten auswählen",
    description=f"Wählt die Quellen mit maximalem Nettonutzen `Σ(gain − cost)` unter gemeinsamem Budget und "
                f"Abhängigkeiten (`requires`). Das verallgemeinert die VOI-Bedingung auf mehrere Quellen und ist eine "
                f"Erweiterung des Modells, kein Satz der Arbeit. Die leere Auswahl ist immer zulässig. Gelöst wird mit dem "
                f"Entscheider des Referenzprojekts `subgraph-sat-solver-econ`; höchstens {MAX_INTEGRATION_OPTIONS} "
                f"Optionen und Werte bis {MAX_INTEGRATION_VALUE}. Kann der Entscheider keine verlässliche Antwort "
                f"liefern, antwortet die API mit HTTP 503.",
    response_model=IntegrationResponse,
    responses={**INPUT_ERRORS, 503: {"model": ErrorResponse, "description": "Der Solver konnte keine verlässliche Antwort liefern."}},
)
def integration_select(request: IntegrationRequest) -> Dict[str, Any]:
    """Löst das Auswahlproblem exakt."""
    options_ = [IntegrationOption(item.name, item.gain, item.cost, tuple(item.requires))
                for item in request.options]
    plan = select_integrations(options_, request.budget)
    return {"selected": list(plan.selected), "net_value": plan.net_value, "total_cost": plan.total_cost,
            "calls": plan.calls}


# --------------------------------------------------------------------------------------------------
# experiments und Fallstudie
# --------------------------------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/experiments/fingerprint",
    tags=["experiments"],
    summary="Fingerprint eines Experimentprotokolls berechnen",
    description="Bildet das reproduzierbare Protokoll aus Name, Konfiguration, Eingaben und Versionen und liefert "
                "dessen SHA-256-Fingerprint. Das Protokoll enthält bewusst keine Zeitstempel; gleiche Eingaben liefern "
                "denselben Fingerprint. Ohne `versions` werden die Versionen des Servers verwendet.",
    response_model=FingerprintResponse,
    responses=INPUT_ERRORS,
)
def fingerprint(request: FingerprintRequest) -> Dict[str, Any]:
    """Berechnet den Fingerprint und gibt das kanonische Protokoll zurück."""
    guard_numbers(request.config, "config")
    guard_numbers(request.inputs, "inputs")
    versions = collect_versions() if request.versions is None else request.versions
    record = ExperimentRecord(as_text("name", request.name), request.config, request.inputs, {}, versions)
    return {"name": record.name, "fingerprint": record.fingerprint(), "versions": dict(versions),
            "record": json.loads(record.to_json())}


@app.get(
    f"{API_PREFIX}/experiments/versions",
    tags=["experiments"],
    summary="Versionen von Python und Abhängigkeiten abrufen",
    description="Gibt die auf dem Server installierten Versionen zurück, die in Fingerprints eingehen. Ein nicht "
                "installiertes Paket steht als `null` da.",
    response_model=VersionsResponse,
)
def versions() -> Dict[str, Any]:
    """Liefert die Versionen von Python und der Abhängigkeiten."""
    return {"versions": collect_versions()}


@app.get(
    f"{API_PREFIX}/case-study",
    tags=["case-study"],
    summary="Fallstudie „Warum sinkt die Marge?“ abrufen",
    description="Gibt die illustrative Fallstudie der Arbeit zurück: Maschinenbauzulieferer, Umsatz 11,0 Mio. €, "
                "Marge 28 % → 24 %, Abweichung 440 T€, aufgeteilt auf Expressfracht, Produktmix und Rabatte. Die Zahlen "
                "stammen aus der Arbeit, die sie auf ein Webinar zurückführt, und sind keine unabhängig erhobenen "
                "Unternehmensdaten. Beträge in T€.",
    response_model=CaseStudyResponse,
)
def case_study() -> Dict[str, Any]:
    """Berechnet die Kennzahlen der Fallstudie."""
    case = margin_case()
    share = case.explained_share
    return {
        "revenue": text(case.revenue), "previous_margin": text(case.previous_margin),
        "current_margin": text(case.current_margin), "expected_db2": text(case.expected_db2),
        "actual_db2": text(case.actual_db2), "gap": text(case.gap),
        "causes": [CaseStudyCause(name=cause.name, amount=text(cause.amount), share=text(cause.amount / case.gap),
                                  explained=text(cause.explained)) for cause in case.causes],
        "explained_share": text(share), "explained_share_percent": round(float(share) * 100, 1),
    }


def run() -> None:
    """Startet den Server (Konsolenaufruf ``aidataeco-api``).

    Host und Port stammen aus ``AIDATAECO_API_HOST`` (Standard ``127.0.0.1``) und
    ``AIDATAECO_API_PORT`` (Standard ``8000``).
    """
    import uvicorn

    uvicorn.run(
        "web.api:app",
        host=os.getenv("AIDATAECO_API_HOST", "127.0.0.1"),
        port=int(os.getenv("AIDATAECO_API_PORT", "8000")),
    )
