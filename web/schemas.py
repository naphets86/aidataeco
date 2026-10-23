"""Request- und Response-Modelle der API (Pydantic) mit Beschreibungen und Beispielen für OpenAPI.

Konventionen:

* **Zahlen** werden als JSON-Zahl oder als Text angenommen (``"3/20"``, ``"0.15"``, ``7``). Alle
  Rechnungen sind exakt (Brüche); Ergebnisse stehen als Bruch-Text (``"3/20"``, ganze Zahlen als ``"3"``).
* **Datumsangaben** sind ISO-Texte ``JJJJ-MM-TT``; der Stichtag ist immer eine Eingabe, nie die Systemuhr.
* **Frei strukturierte Dokumente** (Spezifikation, Antworten, Berichte) haben dieselben Schlüssel wie die
  JSON-/YAML-Dateien der Kommandozeile und werden von der Bibliothek streng geprüft.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr

#: Obergrenze der Optionen je Auswahlproblem (die Rechenzeit des Solvers wächst stark mit der Optionszahl: bei 10 Optionen etwa 2 Sekunden, bei 12 bereits rund 25).
MAX_INTEGRATION_OPTIONS = 10
#: Obergrenze für Nutzen, Kosten und Budget einer Integrationsoption (ganzzahlige Einheiten, z. B. T€).
MAX_INTEGRATION_VALUE = 100_000

Number = Annotated[
    Union[StrictInt, StrictFloat, StrictStr],
    Field(description="Exakte Zahl als JSON-Zahl oder Text, z. B. `7`, `0.15` oder `\"3/20\"`. "
                      "Exponenten sind nur bis 3 Ziffern zulässig (`\"1e100\"`).",
          examples=["3/20"]),
]
LevelName = Literal["HINT", "CROSS_CHECK", "DECISION_PREPARATION", "AUTOMATED_ACTION"]
Level = Union[Annotated[StrictInt, Field(ge=1, le=4)], LevelName]
CauseName = Literal["MISSING_SOURCE", "MISSING_ATTRIBUTE", "UNCLEAR_DEFINITION", "STALE_DATA",
                    "INCOMPLETE_OWN_ANALYSIS"]
IsoDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2026-10-22"],
                               description="Datum im Format `JJJJ-MM-TT`.")]

# --------------------------------------------------------------------------------------------------
# Beispiele (illustrativ, aus der Fallstudie der Arbeit)
# --------------------------------------------------------------------------------------------------

_EDGE = {"source": "orders", "target": "freight",
         "transformation": "orders.delivery_id = freight.delivery_id"}

EXAMPLE_SPEC: Dict[str, Any] = {
    "network": {
        "nodes": [
            {"name": "orders", "attributes": ["order_id", "revenue"], "quality": "9/10",
             "updated": "2026-10-20"},
            {"name": "freight", "attributes": ["delivery_id", "express_cost"], "quality": "4/5",
             "updated": "2026-10-21"},
        ],
        "edges": [_EDGE],
    },
    "product": {
        "name": "Sales Result 360",
        "nodes": ["orders", "freight"],
        "edges": [_EDGE],
        "meaning": {"definitions": {"DB II": "DB I abzüglich Fracht"}, "synonyms": {"Marge": "DB II"},
                    "rules": ["Fracht wird der Lieferung zugeordnet"]},
        "label": {"owner": "Controlling", "version": "1.0", "frequency_days": 7},
        "required_links": [["orders", "freight"]],
        "kpis": ["Marge"],
    },
    "accountabilities": {"data_owner": "Leitung Controlling", "data_product_owner": "Datenteam",
                         "use_case_owner": "Fachbereich Vertrieb"},
    "use_case": {
        "level": "DECISION_PREPARATION",
        "error_budget": {"stakes": 440, "epsilon": "1/20"},
        "min_pass_rate": "3/4",
        "reference_cases": [
            {"question": "Betrag Expressfracht (T€)?", "reference": 230, "tolerance": 10, "weight": 3},
            {"question": "Betrag Rabatte (T€)?", "reference": 60, "tolerance": 5},
        ],
    },
    "evidence": {"human_decides": True},
}

_PROVENANCE = {"sources": [["orders", "1.0"]], "cutoff": "2026-10-21", "rules": ["DB II"]}

EXAMPLE_ANSWERS: Dict[str, Any] = {
    "Betrag Expressfracht (T€)?": {"value": 0, "provenance": _PROVENANCE},
    "Betrag Rabatte (T€)?": {"value": 60, "provenance": _PROVENANCE},
}

# --------------------------------------------------------------------------------------------------
# Fehler und Meta
# --------------------------------------------------------------------------------------------------


class ErrorDetails(BaseModel):
    type: str = Field(description="Fehlerkategorie: `input_error` (ungültige Eingabe), `payload_too_large`, "
                                  "`invalid_header` oder `backend_error`.", examples=["input_error"])
    message: str = Field(description="Menschenlesbare Erklärung des Fehlers.",
                         examples=["Spezifikation: Pflichtfeld fehlt: network"])


class ErrorResponse(BaseModel):
    error: ErrorDetails = Field(description="Strukturierte Fehlerdetails.")


class ValidationErrorResponse(BaseModel):
    detail: List[Dict[str, Any]] = Field(
        description="FastAPI-Validierungsfehler mit Feldpfad, Meldung und Fehlerkategorie.")


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(description="`ok`, wenn der API-Prozess Anfragen beantwortet.", examples=["ok"])


class LevelOption(BaseModel):
    number: int = Field(description="Nummer der Vertrauensstufe (1 bis 4).", examples=[3])
    name: str = Field(description="Name der Stufe, wie ihn Spezifikation und Berichte verwenden.",
                      examples=["DECISION_PREPARATION"])
    role: str = Field(description="Rolle der KI auf dieser Stufe.", examples=["Vorbereitung von Entscheidungen"])


class LimitsResponse(BaseModel):
    max_body_bytes: int = Field(description="Größte zulässige Request-Größe (`Content-Length`) in Bytes.")
    max_integration_options: int = Field(description="Größte Optionszahl für `POST /api/v1/integration/select`.")
    max_integration_value: int = Field(description="Größter Wert für Nutzen, Kosten und Budget der Optionen.")
    max_exponent_digits: int = Field(description="Größte Ziffernzahl eines Exponenten in Zahlentexten.")


class OptionsResponse(BaseModel):
    levels: List[LevelOption] = Field(description="Die vier Vertrauensstufen.")
    measured_evidence: List[str] = Field(
        description="Nachweise, die aus den Daten abgeleitet werden und in einer Spezifikation nicht erklärt werden dürfen.")
    declared_evidence: List[str] = Field(
        description="Organisatorische Nachweise, die eine Spezifikation unter `evidence` erklären darf.")
    deviation_causes: List[str] = Field(description="Namen der möglichen Abweichungsursachen.")
    directions: List[str] = Field(description="Richtungen einer Kennzahländerung im Berichtsvergleich.")
    limits: LimitsResponse = Field(description="Eingabegrenzen der API.")


# --------------------------------------------------------------------------------------------------
# Freigabebericht, Antworten, Spezifikation, Vergleich
# --------------------------------------------------------------------------------------------------


class SpecRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"spec": EXAMPLE_SPEC}]})

    spec: Dict[str, Any] = Field(
        description="Spezifikation des Data Products mit Anwendungsfall; dieselben Schlüssel wie die "
                    "YAML-/JSON-Datei der Kommandozeile. Pflicht sind `network`, `product` und `use_case`; "
                    "optional sind `accountabilities` und `evidence`. Messbare Nachweise (`kpis_defined`, "
                    "`provenance_available`, `quality_measurable`, `error_budget_met`) dürfen nicht erklärt werden.",
        examples=[EXAMPLE_SPEC])


class SpecSummary(BaseModel):
    product: str = Field(description="Name des Data Products.", examples=["Sales Result 360"])
    version: str = Field(description="Version aus dem Label.", examples=["1.0"])
    owner: str = Field(description="Owner aus dem Label.", examples=["Controlling"])
    level: str = Field(description="Angestrebte Stufe als Name.", examples=["DECISION_PREPARATION"])
    level_number: int = Field(description="Angestrebte Stufe als Nummer.", examples=[3])
    nodes: List[str] = Field(description="Knoten `V_P` des Data Products, alphabetisch.")
    required_links: List[List[str]] = Field(description="Geforderte Verknüpfungen als Knotenpaare.")
    kpis: List[str] = Field(description="Kennzahlbegriffe, die definiert sein müssen.")
    reference_cases: int = Field(description="Anzahl der Referenzfragen.", examples=[2])
    error_budget_limit: Optional[str] = Field(description="Zulässiger Verlust `ε·W` als Bruch-Text oder `null`, "
                                                          "wenn kein Error Budget festgelegt ist.", examples=["22"])
    min_pass_rate: Optional[str] = Field(description="Mindest-Bestehensquote als Bruch-Text oder `null`.",
                                         examples=["3/4"])
    missing_accountabilities: List[str] = Field(description="Rollen ohne benannte Person.")
    declared_evidence: Dict[str, bool] = Field(description="Erklärte organisatorische Nachweise.")


class SpecValidationResponse(BaseModel):
    valid: Literal[True] = Field(description="Immer `true`; ungültige Spezifikationen antworten mit HTTP 422.")
    summary: SpecSummary = Field(description="Zusammenfassung der gelesenen Spezifikation.")


class ReportRequest(SpecRequest):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "spec": EXAMPLE_SPEC, "answers": EXAMPLE_ANSWERS, "today": "2026-10-22", "expected_loss": 5}]})

    answers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Antworten der KI je Referenzfrage: `{Frage: {\"value\": Zahl|null, \"provenance\": "
                    "{\"sources\": [[Quelle, Version]], \"cutoff\": Datum, \"rules\": [Regel]}}}`. Fehlende Fragen "
                    "gelten als unbeantwortet; Fragen, die kein Referenzfall kennt, sind ein Fehler.",
        examples=[EXAMPLE_ANSWERS])
    today: IsoDate = Field(description="Stichtag der Prüfung. Er ist Eingabe, damit der Bericht reproduzierbar bleibt.")
    expected_loss: Optional[Number] = Field(
        default=None,
        description="Erwarteter Verlust `E[L(ŷ, y*)]`. Ohne Angabe gilt das Error Budget als nicht belegt; "
                    "ohne Error Budget in der Spezifikation ist die Angabe ein Fehler.")
    versions: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Versionen von Python und Abhängigkeiten für den Fingerprint. Ohne Angabe werden sie "
                    "auf dem Server ermittelt; für einen reproduzierbaren Fingerprint sollten sie angegeben werden.",
        examples=[{"python": "3.12.0", "subgraph-sat-solver-econ": "2.0.0"}])


class EvaluationModel(BaseModel):
    pass_rate: str = Field(description="Gewichtete Bestehensquote als Bruch-Text.", examples=["3/4"])
    provenance_coverage: str = Field(description="Anteil der Antworten mit vollständiger Provenance.", examples=["1"])
    unanswered: int = Field(description="Anzahl unbeantworteter Fragen.", examples=[0])


class NodeStatusModel(BaseModel):
    name: str = Field(description="Name des Knotens.", examples=["orders"])
    quality: Optional[str] = Field(description="Qualität `q_v ∈ [0,1]` als Bruch-Text; `null`, wenn unbekannt.",
                                   examples=["9/10"])
    updated: Optional[str] = Field(description="Letzte Aktualisierung `t_v`; `null`, wenn unbekannt.",
                                   examples=["2026-10-20"])
    fresh: Optional[bool] = Field(description="Aktuell zum Stichtag; `null`, solange die Aktualisierung unbekannt ist.")


class EvidenceModel(BaseModel):
    kpis_defined: bool = Field(default=False, description="Kennzahlen definiert und verknüpft (gemessen).")
    provenance_available: bool = Field(default=False, description="Provenance aller Antworten vollständig (gemessen).")
    quality_measurable: bool = Field(default=False, description="Qualität aller Knoten bekannt (gemessen).")
    error_budget_met: bool = Field(default=False, description="Erwarteter Verlust innerhalb `ε·W` (gemessen).")
    human_decides: bool = Field(default=False, description="Ein Mensch entscheidet (erklärt).")
    explicit_approval: bool = Field(default=False, description="Ausdrückliche Freigabe liegt vor (erklärt).")
    logging: bool = Field(default=False, description="Protokollierung ist eingerichtet (erklärt).")
    intervention_path: bool = Field(default=False, description="Eingriffspfad ist festgelegt (erklärt).")


class ReportResponse(BaseModel):
    product: str = Field(description="Name des Data Products.")
    version: str = Field(description="Version aus dem Label.")
    owner: str = Field(description="Owner aus dem Label.")
    level: str = Field(description="Angestrebte Stufe als Name.", examples=["DECISION_PREPARATION"])
    today: str = Field(description="Stichtag der Prüfung.", examples=["2026-10-22"])
    missing_links: List[List[str]] = Field(description="Geforderte Verknüpfungen, die im Data Product nicht nachweisbar sind.")
    nodes: List[NodeStatusModel] = Field(description="Zustand der Knoten von `V_P`, alphabetisch.")
    evaluation: Optional[EvaluationModel] = Field(description="Kennzahlen der Referenzfragen; `null` ohne Referenzfragen.")
    min_pass_rate: Optional[str] = Field(description="Mindest-Bestehensquote oder `null`.")
    expected_loss: Optional[str] = Field(description="Übergebener erwarteter Verlust oder `null`.")
    budget_limit: Optional[str] = Field(description="Zulässiger Verlust `ε·W` oder `null`.")
    evidence: EvidenceModel = Field(description="Abgeleitete und erklärte Nachweise.")
    blocked: bool = Field(description="`true`, wenn mindestens ein Freigabehindernis besteht. "
                                      "`false` ist keine Freigabe, nur die Feststellung, dass keine formalisierte Bedingung verletzt ist.")
    blockers: List[str] = Field(description="Freigabehindernisse im Klartext.")
    versions: Dict[str, Optional[str]] = Field(description="Versionen von Python und Abhängigkeiten; `null` = nicht installiert.")
    fingerprint: str = Field(description="SHA-256 über Spezifikation, Antworten, Stichtag, erwarteten Verlust und Versionen.")


class CasesRequest(SpecRequest):
    model_config = ConfigDict(json_schema_extra={"examples": [{"spec": EXAMPLE_SPEC, "answers": EXAMPLE_ANSWERS}]})

    answers: Dict[str, Any] = Field(default_factory=dict, description="Antworten je Referenzfrage wie bei `POST /api/v1/reports`.",
                                    examples=[EXAMPLE_ANSWERS])


class CaseResult(BaseModel):
    question: str = Field(description="Referenzfrage.")
    reference: str = Field(description="Referenzwert `y*` als Bruch-Text.")
    tolerance: str = Field(description="Toleranz `δ` als Bruch-Text.")
    weight: str = Field(description="Gewicht `w` als Bruch-Text.")
    value: Optional[str] = Field(description="Antwort `ŷ` als Bruch-Text; `null`, wenn keine Antwort vorliegt.")
    answered: bool = Field(description="Ob eine Antwort vorliegt.")
    passed: bool = Field(description="`|ŷ − y*| ≤ δ`; ohne Antwort `false`.")
    provenance_complete: bool = Field(description="Ob Quelle, Datenstichtag und Definition vorliegen.")
    provenance_missing: List[str] = Field(description="Fehlende Bestandteile der Provenance (`Quelle`, `Datenstichtag`, `Definition`).")


class CasesResponse(BaseModel):
    cases: List[CaseResult] = Field(description="Ergebnis je Referenzfrage in der Reihenfolge der Spezifikation.")
    evaluation: Optional[EvaluationModel] = Field(description="Aggregierte Kennzahlen; `null` ohne Referenzfragen.")


class ReportCompareRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"old": {"…": "Ausgabe von POST /api/v1/reports"},
                                                              "new": {"…": "Ausgabe von POST /api/v1/reports"}}]})

    old: Dict[str, Any] = Field(description="Früherer Bericht, so wie `POST /api/v1/reports` ihn ausgibt.")
    new: Dict[str, Any] = Field(description="Späterer Bericht desselben Data Products.")


class ChangeModel(BaseModel):
    metric: str = Field(description="Name der Kennzahl.", examples=["Bestehensquote"])
    before: Optional[str] = Field(description="Wert im früheren Bericht; `null` = nicht belegt.")
    after: Optional[str] = Field(description="Wert im späteren Bericht; `null` = nicht belegt.")
    direction: Literal["IMPROVED", "UNCHANGED", "REGRESSED"] = Field(description="Richtung der Änderung.")


class ComparisonResponse(BaseModel):
    product: str = Field(description="Name des Data Products.")
    version_before: str = Field(description="Version im früheren Bericht.")
    version_after: str = Field(description="Version im späteren Bericht.")
    level_before: str = Field(description="Stufe im früheren Bericht.")
    level_after: str = Field(description="Stufe im späteren Bericht.")
    fingerprint_changed: bool = Field(description="Ob sich die Eingaben (Fingerprint) geändert haben.")
    changes: List[ChangeModel] = Field(description="Sieben Kennzahlen mit Richtung.")
    new_blockers: List[str] = Field(description="Freigabehindernisse, die neu hinzugekommen sind.")
    resolved_blockers: List[str] = Field(description="Freigabehindernisse, die behoben wurden.")
    has_regression: bool = Field(description="`true`, wenn sich eine Kennzahl verschlechtert oder ein Hindernis neu hinzukommt.")


# --------------------------------------------------------------------------------------------------
# Auswertung (Fortschritt messen)
# --------------------------------------------------------------------------------------------------


class ProvenanceModel(BaseModel):
    sources: List[Annotated[List[str], Field(min_length=2, max_length=2)]] = Field(
        default_factory=list, description="Quellen als `[Name, Version]`.", examples=[[["orders", "1.0"]]])
    cutoff: Optional[IsoDate] = Field(default=None, description="Datenstichtag der Antwort.")
    rules: List[str] = Field(default_factory=list, description="Angewendete Regeln oder Definitionen.", examples=[["DB II"]])


class AnswerModel(BaseModel):
    value: Optional[Number] = Field(description="Antwort `ŷ`; `null`, wenn keine Antwort vorliegt.")
    provenance: Optional[ProvenanceModel] = Field(default=None, description="Provenance der Antwort.")


class CaseModel(BaseModel):
    question: str = Field(description="Referenzfrage `q`; muss eindeutig sein.", examples=["Betrag Expressfracht (T€)?"])
    reference: Number = Field(description="Fachlich geprüfter Referenzwert `y*`.")
    tolerance: Number = Field(description="Toleranz `δ ≥ 0`.")
    weight: Number = Field(default=1, description="Ökonomisches Gewicht `w ≥ 0`; die Summe muss positiv sein.")


class PassRateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "cases": [{"question": "F1", "reference": 10, "tolerance": 1},
                  {"question": "F2", "reference": 20, "tolerance": 2, "weight": 3}],
        "answers": {"F1": {"value": 10, "provenance": _PROVENANCE}, "F2": {"value": 25}}}]})

    cases: List[CaseModel] = Field(description="Referenzfragen mit Referenzwert, Toleranz und Gewicht.")
    answers: Dict[str, AnswerModel] = Field(
        default_factory=dict, description="Antworten je Frage; fehlende Fragen gelten als unbeantwortet.")


class PassRateResponse(BaseModel):
    cases: List[CaseResult] = Field(description="Ergebnis je Referenzfrage.")
    evaluation: EvaluationModel = Field(description="Bestehensquote, Provenance-Abdeckung und unbeantwortete Fragen.")


class CauseModel(BaseModel):
    name: str = Field(description="Name der Ursache.", examples=["Expressfracht"])
    amount: Number = Field(description="Betrag der Ursache `≥ 0`.", examples=[230])
    explained: Number = Field(description="Von der KI erklärter Anteil in `[0, 1]`.", examples=[0])


class ExplainedShareRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"causes": [
        {"name": "Expressfracht", "amount": 230, "explained": 0}, {"name": "Produktmix", "amount": 150, "explained": 0},
        {"name": "Rabatte", "amount": 60, "explained": 1}]}]})

    causes: List[CauseModel] = Field(description="Ursachen des bekannten Effekts.")
    total_effect: Optional[Number] = Field(
        default=None, description="Bekannter Gesamteffekt. Ohne Angabe ist es die Summe der Beträge; ein größerer "
                                  "Wert lässt einen nicht zugeordneten Rest unerklärt.")


class ExplainedShareResponse(BaseModel):
    explained_share: str = Field(description="Erklärter Anteil am Gesamteffekt als Bruch-Text.", examples=["3/22"])
    unexplained_share: str = Field(description="`1 − erklärter Anteil`.", examples=["19/22"])
    explained_amount: str = Field(description="Summe `Betrag·erklärter Anteil` aller Ursachen.", examples=["60"])
    total_effect: str = Field(description="Verwendeter Gesamteffekt.", examples=["440"])


class CompletenessRequest(BaseModel):
    rows: List[Dict[str, Any]] = Field(description="Datenzeilen; mindestens eine.",
                                       examples=[[{"product_group": "A"}, {"product_group": ""}, {"product_group": None}]])
    attribute: str = Field(description="Kritisches Attribut, dessen Belegung geprüft wird.", examples=["product_group"])


class CompletenessResponse(BaseModel):
    completeness: str = Field(description="Belegungsgrad als Bruch-Text; `null` und leere Texte gelten als nicht belegt.",
                              examples=["1/3"])
    rows: int = Field(description="Anzahl der geprüften Zeilen.", examples=[3])
    filled: int = Field(description="Anzahl der Zeilen mit belegtem Attribut.", examples=[1])


class FreshnessRequest(BaseModel):
    updated: Optional[IsoDate] = Field(description="Letzte Aktualisierung; `null`, wenn unbekannt.")
    frequency_days: StrictInt = Field(description="Zugesagte Aktualisierungsfrequenz in Tagen (`> 0`).", examples=[7])
    today: IsoDate = Field(description="Stichtag.")


class FreshnessResponse(BaseModel):
    fresh: bool = Field(description="`true`, wenn die letzte Aktualisierung höchstens `frequency_days` zurückliegt; "
                                    "unbekannte oder in der Zukunft liegende Aktualisierung gilt als nicht aktuell.")
    age_days: Optional[int] = Field(description="Alter der Daten in Tagen; `null`, wenn die Aktualisierung unbekannt ist.")


# --------------------------------------------------------------------------------------------------
# Error Budget
# --------------------------------------------------------------------------------------------------


class BudgetCheckRequest(BaseModel):
    stakes: Number = Field(description="Stakes `W ≥ 0` der Entscheidung.", examples=[440])
    epsilon: Number = Field(description="Anteil `ε > 0`.", examples=["1/20"])
    expected_loss: Number = Field(description="Erwarteter Verlust `E[L(ŷ, y*)] ≥ 0`.", examples=[20])


class BudgetCheckResponse(BaseModel):
    limit: str = Field(description="Zulässiger Verlust `ε·W`.", examples=["22"])
    expected_loss: str = Field(description="Übergebener erwarteter Verlust.", examples=["20"])
    good_enough: bool = Field(description="Gut-genug-Bedingung `E[L] ≤ ε·W`.")
    headroom: str = Field(description="`ε·W − E[L]`; negativ, wenn das Budget überschritten ist.", examples=["2"])


class LinearLossRequest(BaseModel):
    cost_per_unit: Number = Field(description="Kostensatz `c ≥ 0` je Einheit Abweichung.", examples=[2])
    expected_abs_error: Number = Field(description="Erwarteter Fehlerbetrag `E|B_miss + B_def + η| ≥ 0`.", examples=[10])
    stakes: Number = Field(description="Stakes `W ≥ 0`.", examples=[440])
    epsilon: Number = Field(description="Anteil `ε > 0`.", examples=["1/20"])


class LinearLossResponse(BaseModel):
    expected_loss: str = Field(description="`c·E|…|`.", examples=["20"])
    limit: str = Field(description="`ε·W`.", examples=["22"])
    good_enough: bool = Field(description="Gut-genug-Bedingung unter linearem Loss.")


class DecompositionRequest(BaseModel):
    b_miss: Number = Field(description="Bias durch fehlende Einflussgrößen `B_miss`.", examples=[-380])
    b_def: Number = Field(description="Bias aus uneinheitlicher Definition `B_def`.", examples=[0])
    eta: Number = Field(description="Zufälliger Fehler `η`.", examples=[5])


class DecompositionResponse(BaseModel):
    total: str = Field(description="Antwortfehler `ŷ − y* = B_miss + B_def + η`.", examples=["-375"])
    expected: str = Field(description="Erwartungswert `B_miss + B_def`.", examples=["-380"])


class MissingBiasRequest(BaseModel):
    effects: Dict[str, Number] = Field(description="Beitrag `α_i·s_i` jeder wesentlichen Einflussgröße `i ∈ S_q`.",
                                       examples=[{"Fracht": 230, "Produktmix": 150, "Rabatt": 60}])
    observed: List[str] = Field(description="Im Netz beobachtbare Einflussgrößen `S̃_q ⊆ S_q`.", examples=[["Rabatt"]])


class MissingBiasResponse(BaseModel):
    b_miss: str = Field(description="`B_miss = −Σ α_i·s_i` über die nicht beobachteten Größen.", examples=["-380"])
    missing: List[str] = Field(description="Nicht beobachtete Einflussgrößen, alphabetisch.")


class LipschitzRequest(BaseModel):
    lipschitz: Number = Field(description="Lipschitz-Konstante `L ≥ 0`.", examples=[2])
    driver_distance: Number = Field(description="Abstand `‖S_q − S̃_q‖ ≥ 0`.", examples=[10])
    b_def: Number = Field(description="Definitionsbias `B_def`.", examples=[-1])
    eta: Number = Field(description="Rauschen `η`.", examples=[2])


class LipschitzResponse(BaseModel):
    bound: str = Field(description="Schranke `L·‖S_q − S̃_q‖ + |B_def| + |η|` für `|ŷ − y*|`.", examples=["23"])


# --------------------------------------------------------------------------------------------------
# Diagnose von Abweichungen
# --------------------------------------------------------------------------------------------------


class PosteriorRequest(BaseModel):
    prior_h1: Number = Field(description="Prior `P(H1)` in `(0, 1)`.", examples=["1/5"])
    likelihood_h1: Number = Field(description="Likelihood `p(d|H1) ≥ 0`.", examples=["3/5"])
    likelihood_h0: Number = Field(description="Likelihood `p(d|H0) > 0`.", examples=["1/5"])


class PosteriorResponse(BaseModel):
    odds: str = Field(description="Posterior Odds `P(H1|d)/P(H0|d)`.", examples=["3/4"])
    probability: str = Field(description="Posterior `P(H1|d)`.", examples=["3/7"])
    increased: bool = Field(description="`true`, wenn die Beobachtung die Wahrscheinlichkeit von `H1` gegenüber dem Prior erhöht.")


class BayesUpdateRequest(BaseModel):
    prior: Dict[str, Number] = Field(description="Prior `π₀(θ)` über einem endlichen Zustandsraum; Summe 1.",
                                     examples=[{"verknüpft": "7/10", "fehlt": "3/10"}])
    likelihood: Dict[str, Number] = Field(description="Likelihood `p(d|θ)` je Zustand; dieselben Zustände wie der Prior.",
                                          examples=[{"verknüpft": "1/10", "fehlt": "9/10"}])


class BayesUpdateResponse(BaseModel):
    posterior: Dict[str, str] = Field(description="Posterior `π₁(θ) ∝ p(d|θ)·π₀(θ)` als Bruch-Text.")


class VoiRequest(BayesUpdateRequest):
    gains: Dict[str, Number] = Field(description="Erwarteter Zusatznutzen `ΔW(θ)` je Zustand.",
                                     examples=[{"verknüpft": 0, "fehlt": 100}])
    cost: Number = Field(description="Integrationskosten `C_int ≥ 0`.", examples=[40])


class VoiResponse(BaseModel):
    posterior: Dict[str, str] = Field(description="Posterior `π₁(θ)`.")
    expected_gain: str = Field(description="`E_{π₁}[ΔW(θ)]`.", examples=["1350/17"])
    cost: str = Field(description="Integrationskosten.", examples=["40"])
    rational: bool = Field(description="VOI-Bedingung `E[ΔW] ≥ C_int`: die Erweiterung ist rational.")


class DeviationCauseModel(BaseModel):
    name: CauseName = Field(description="Technischer Name der Ursache.")
    label: str = Field(description="Bezeichnung der Ursache.", examples=["Fehlende Datenquelle"])
    response: str = Field(description="Geeignete Reaktion.")


class DeviationCausesResponse(BaseModel):
    causes: List[DeviationCauseModel] = Field(description="Mögliche Ursachen einer Abweichung mit Reaktion.")


class DeviationModel(BaseModel):
    cause: CauseName = Field(description="Ursache der Abweichung.")
    outcome: Optional[str] = Field(default=None, description="Dokumentierte Korrektur oder begründete Bestätigung; "
                                                              "`null` oder leer = noch nicht bearbeitet.")


class DeviationsRequest(BaseModel):
    deviations: List[DeviationModel] = Field(description="Abweichungen zwischen KI-Antwort und interner Analyse.",
                                             examples=[[{"cause": "MISSING_SOURCE", "outcome": "Frachtdaten angebunden"},
                                                        {"cause": "STALE_DATA"}]])


class DeviationItem(BaseModel):
    cause: CauseName = Field(description="Technischer Name der Ursache.")
    label: str = Field(description="Bezeichnung der Ursache.")
    response: str = Field(description="Geeignete Reaktion.")
    processed: bool = Field(description="Ob ein Ergebnis dokumentiert ist.")


class DeviationsResponse(BaseModel):
    total: int = Field(description="Anzahl der Abweichungen.")
    processed: int = Field(description="Kennzahl „Bearbeitete Abweichungen“: Anzahl mit dokumentiertem Ergebnis.")
    open: int = Field(description="Noch nicht bearbeitete Abweichungen.")
    items: List[DeviationItem] = Field(description="Abweichungen in der übergebenen Reihenfolge.")


# --------------------------------------------------------------------------------------------------
# Vertrauensstufen und Freigabe
# --------------------------------------------------------------------------------------------------


class LevelDescription(LevelOption):
    requirements: List[str] = Field(description="Nachweise, die diese Stufe verlangt (einschließlich der niedrigeren Stufen).")


class LevelsResponse(BaseModel):
    levels: List[LevelDescription] = Field(description="Die vier Stufen mit ihren Anforderungen.")


class AccountabilitiesModel(BaseModel):
    data_owner: Optional[str] = Field(default=None, description="Data Owner: Bedeutung und Kennzahlen.")
    data_product_owner: Optional[str] = Field(default=None, description="Data Product Owner: Lieferung und Qualität.")
    use_case_owner: Optional[str] = Field(default=None, description="Use-Case Owner: Freigabe, Testfragen, Error Budget.")


class BlockersRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "level": "DECISION_PREPARATION",
        "accountabilities": {"data_owner": "A", "data_product_owner": "B"},
        "evidence": {"kpis_defined": True, "human_decides": True}}]})

    level: Level = Field(description="Angestrebte Stufe als Nummer (1–4) oder Name.", examples=["DECISION_PREPARATION"])
    accountabilities: AccountabilitiesModel = Field(default_factory=AccountabilitiesModel,
                                                    description="Benannte Verantwortliche; nicht benannte Rollen blockieren jede Stufe.")
    evidence: EvidenceModel = Field(default_factory=EvidenceModel,
                                    description="Vorliegende Nachweise; nicht genannte Nachweise gelten als nicht belegt.")


class BlockersResponse(BaseModel):
    level: str = Field(description="Geprüfte Stufe als Name.")
    level_number: int = Field(description="Geprüfte Stufe als Nummer.")
    blocked: bool = Field(description="`true`, wenn mindestens ein Freigabehindernis besteht (keine Freigabe bei `false`).")
    blockers: List[str] = Field(description="Gründe, die eine Freigabe auf dieser Stufe verhindern.")


# --------------------------------------------------------------------------------------------------
# Datenquellen, Experimente, Fallstudie
# --------------------------------------------------------------------------------------------------


class IntegrationOptionModel(BaseModel):
    name: str = Field(description="Name der Quelle; eindeutig.", examples=["Fracht"])
    gain: StrictInt = Field(ge=0, le=MAX_INTEGRATION_VALUE, description="Erwarteter Zusatznutzen `E[ΔW]` (ganzzahlige Einheiten, z. B. T€).",
                            examples=[230])
    cost: StrictInt = Field(ge=0, le=MAX_INTEGRATION_VALUE, description="Integrationskosten `C_int` (dieselben Einheiten).",
                            examples=[80])
    requires: List[str] = Field(default_factory=list, description="Quellen, die ebenfalls integriert sein müssen.",
                                examples=[["Auftraege"]])


class IntegrationRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "options": [{"name": "Auftraege", "gain": 0, "cost": 20},
                    {"name": "Fracht", "gain": 230, "cost": 80, "requires": ["Auftraege"]},
                    {"name": "Produktgruppe", "gain": 150, "cost": 60}],
        "budget": 120}]})

    options: List[IntegrationOptionModel] = Field(max_length=MAX_INTEGRATION_OPTIONS,
                                                  description=f"Mögliche Integrationen, höchstens {MAX_INTEGRATION_OPTIONS}.")
    budget: Optional[StrictInt] = Field(default=None, ge=0, le=MAX_INTEGRATION_VALUE,
                                        description="Gemeinsames Budget für die Kosten; ohne Angabe unbeschränkt.")


class IntegrationResponse(BaseModel):
    selected: List[str] = Field(description="Gewählte Quellen in der Reihenfolge der Eingabe.")
    net_value: int = Field(description="Nettonutzen `Σ(gain − cost)` der Auswahl; nie negativ.")
    total_cost: int = Field(description="Gesamtkosten der gewählten Quellen.")
    calls: int = Field(description="Anzahl der Entscheideraufrufe des Solvers.")


class FingerprintRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "name": "lauf-1", "config": {"epsilon": "1/20"}, "inputs": {"today": "2026-10-22"},
        "versions": {"python": "3.12.0"}}]})

    name: str = Field(description="Experimentname; ein einfacher Dateiname ohne Pfadanteile.", examples=["lauf-1"])
    config: Dict[str, Any] = Field(default_factory=dict, description="Konfiguration des Experiments.")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Eingaben des Experiments.")
    versions: Optional[Dict[str, Optional[str]]] = Field(
        default=None, description="Versionen für den Fingerprint; ohne Angabe die des Servers.")


class FingerprintResponse(BaseModel):
    name: str = Field(description="Experimentname.")
    fingerprint: str = Field(description="SHA-256 über Name, Konfiguration, Eingaben und Versionen.")
    versions: Dict[str, Optional[str]] = Field(description="Verwendete Versionen.")
    record: Dict[str, Any] = Field(description="Vollständiges Protokoll (ohne Resultate) in kanonischer Form.")


class VersionsResponse(BaseModel):
    versions: Dict[str, Optional[str]] = Field(description="Versionen von Python und Abhängigkeiten; `null` = nicht installiert.")


class CaseStudyCause(BaseModel):
    name: str = Field(description="Ursache der DB-II-Abweichung.", examples=["Expressfracht"])
    amount: str = Field(description="Betrag in T€.", examples=["230"])
    share: str = Field(description="Anteil an der Abweichung als Bruch-Text.", examples=["23/44"])
    explained: str = Field(description="Von der KI erklärter Anteil dieser Ursache.", examples=["0"])


class CaseStudyResponse(BaseModel):
    revenue: str = Field(description="Aktueller Umsatz in T€.", examples=["11000"])
    previous_margin: str = Field(description="Marge des Vorjahres.", examples=["7/25"])
    current_margin: str = Field(description="Aktuelle Marge.", examples=["6/25"])
    expected_db2: str = Field(description="DB II bei Vorjahresmarge in T€.", examples=["3080"])
    actual_db2: str = Field(description="Tatsächlicher DB II in T€.", examples=["2640"])
    gap: str = Field(description="Differenz in T€.", examples=["440"])
    causes: List[CaseStudyCause] = Field(description="Aufteilung der Abweichung auf Ursachen.")
    explained_share: str = Field(description="Von der KI erklärter Anteil der Abweichung.", examples=["3/22"])
    explained_share_percent: float = Field(description="Erklärter Anteil in Prozent (gerundet auf eine Nachkommastelle).",
                                           examples=[13.6])
