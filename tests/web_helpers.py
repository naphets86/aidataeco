"""Gemeinsame Hilfen der Web-API-Tests: Client, JSON-fähige Beispieldaten und Pfade."""

import json

from fastapi.testclient import TestClient

from web.api import API_PREFIX, app

from sample_data import as_json, base_answers, base_data

client = TestClient(app)


def url(path):
    """Vollständiger Pfad eines Endpunkts, z. B. ``url("/reports")``."""
    return f"{API_PREFIX}{path}"


def jsonable(data):
    """Beispieldaten ohne ``date``-Objekte, wie sie als JSON übertragen werden."""
    return json.loads(as_json(data))


def spec():
    return jsonable(base_data())


def answers():
    return jsonable(base_answers())


def report_request(**changes):
    """Gültige Berichtsanfrage (Stufe 3, alle Nachweise erfüllt); ``changes`` überschreibt Felder."""
    body = {"spec": spec(), "answers": answers(), "today": "2026-10-22", "expected_loss": 5,
            "versions": {"python": "3.11.0", "subgraph-sat-solver-econ": None}}
    body.update(changes)
    return body


def post(path, body):
    return client.post(url(path), json=body)
