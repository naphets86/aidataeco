"""Gemeinsame Beispieldaten der Tests: eine vollständig „gute" Spezifikation samt Antworten."""

import copy
import json
from datetime import date

TODAY = date(2026, 10, 22)
Q1 = "Frage 1"
Q2 = "Frage 2"

_EDGE = {"source": "orders", "target": "freight", "transformation": "orders.delivery_id = freight.delivery_id"}

_BASE = {
    "network": {
        "nodes": [
            {"name": "orders", "attributes": ["order_id", "revenue"], "quality": "9/10",
             "updated": "2026-10-20"},
            {"name": "freight", "attributes": ["delivery_id"], "quality": "4/5",
             "updated": date(2026, 10, 21)},
        ],
        "edges": [_EDGE],
    },
    "product": {
        "name": "Sales Result 360",
        "nodes": ["orders", "freight"],
        "edges": [_EDGE],
        "meaning": {
            "definitions": {"DB II": "DB I abzüglich Fracht"},
            "synonyms": {"Marge": "DB II"},
            "rules": ["Fracht wird der Lieferung zugeordnet"],
        },
        "label": {"owner": "Controlling", "version": "1.0", "frequency_days": 7},
        "required_links": [["orders", "freight"]],
        "kpis": ["Marge"],
    },
    "accountabilities": {"data_owner": "A", "data_product_owner": "B", "use_case_owner": "C"},
    "use_case": {
        "level": "DECISION_PREPARATION",
        "error_budget": {"stakes": 100, "epsilon": "1/10"},
        "min_pass_rate": "1/2",
        "reference_cases": [
            {"question": Q1, "reference": 10, "tolerance": 1},
            {"question": Q2, "reference": 20, "tolerance": 2, "weight": 3},
        ],
    },
    "evidence": {"human_decides": True, "explicit_approval": True, "logging": True,
                 "intervention_path": True},
}

_PROVENANCE = {"sources": [["orders", "1.0"]], "cutoff": "2026-10-21", "rules": ["DB II"]}
_ANSWERS = {Q1: {"value": 10, "provenance": _PROVENANCE},
            Q2: {"value": "21", "provenance": _PROVENANCE}}


def base_data():
    """Tiefe Kopie der guten Spezifikation; Tests verändern nur die Kopie."""
    return copy.deepcopy(_BASE)


def base_answers():
    """Tiefe Kopie guter Antworten (beide Fragen innerhalb der Toleranz, Provenance vollständig)."""
    return copy.deepcopy(_ANSWERS)


def as_json(data):
    """JSON-Text einer Spezifikation oder Antwort (Datumsobjekte werden zu ISO-Text)."""
    return json.dumps(data, default=str)
