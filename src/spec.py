"""Maschinenlesbare Spezifikation eines Data Products mit Anwendungsfall (Abschnitt „Operationalisierung").

Eine Spezifikation (JSON oder YAML) beschreibt Datennetz, Data Product, Verantwortliche und den
Anwendungsfall mit Stufe, Error Budget und Referenzfragen. Sie wird zu den Objekten aus
:mod:`model`, :mod:`governance`, :mod:`errorbudget` und :mod:`evaluation` gelesen.

Zwei Leitplanken:

* Nachweise, die sich messen lassen (Kennzahlen, Provenance, Qualität, Error Budget), dürfen in
  der Spezifikation **nicht** erklärt werden; sie werden aus den Daten abgeleitet. Erklärt werden
  nur organisatorische Nachweise (:data:`ORGANIZATIONAL`).
* Verantwortliche werden nie implizit vorbelegt; fehlende Angaben bleiben ``None``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple, Union

from .errorbudget import ErrorBudget
from .evaluation import ReferenceCase
from .governance import Accountabilities, Evidence, ReliabilityLevel
from .model import (Answer, DataNetwork, DataProduct, Edge, Label, Meaning, Node, Provenance,
                    unit_fraction)
from .parsing import (as_bool, as_date, as_fraction, as_int, as_list, as_mapping, as_text,
                      check_keys, optional)
from .provider import StaticProvider, collect_answers

#: Nachweise, die der Anwender erklärt (organisatorisch, nicht aus Daten messbar).
ORGANIZATIONAL = ("human_decides", "explicit_approval", "logging", "intervention_path")
#: Nachweise, die aus den Daten abgeleitet werden und deshalb nicht erklärbar sind.
MEASURED = ("kpis_defined", "provenance_available", "quality_measurable", "error_budget_met")


@dataclass(frozen=True)
class UseCase:
    """Anwendungsfall: angestrebte Stufe, Error Budget, Referenzfragen, Mindest-Bestehensquote."""

    level: ReliabilityLevel
    budget: Optional[ErrorBudget]
    cases: Tuple[ReferenceCase, ...]
    min_pass_rate: Optional[Fraction]


@dataclass(frozen=True)
class Spec:
    """Gelesene Spezifikation; ``raw`` ist die unveränderte Eingabe (für den Fingerprint)."""

    product: DataProduct
    required_links: Tuple[Tuple[str, str], ...]
    kpis: Tuple[str, ...]
    accountabilities: Accountabilities
    use_case: UseCase
    declared: Evidence
    raw: Mapping[str, object]


def read_document(path: Union[str, Path]) -> Mapping[str, object]:
    """Liest eine ``.json``-, ``.yaml``- oder ``.yml``-Datei (UTF-8) als Mapping.

    YAML benötigt PyYAML (``pip install aidataeco[yaml]``); fehlt es, folgt ``ValueError``.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".json", ".yaml", ".yml"):
        raise ValueError(f"Unbekanntes Dateiformat {path.suffix!r} (erwartet: .json, .yaml, .yml)")
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ImportError:
            raise ValueError("YAML benötigt PyYAML (pip install aidataeco[yaml])") from None
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise ValueError(f"{path.name}: ungültiges YAML: {error}") from None
    return as_mapping(path.name, data)


def _texts(name: str, value: object) -> Tuple[str, ...]:
    return tuple(as_text(f"{name}[{i}]", item) for i, item in enumerate(as_list(name, value)))


def _text_map(name: str, value: object) -> Dict[str, str]:
    return {as_text(f"{name}-Schlüssel", key): as_text(f"{name}[{key!r}]", item)
            for key, item in as_mapping(name, value).items()}


def _node(name: str, data: object) -> Node:
    mapping = as_mapping(name, data)
    check_keys(name, mapping, ("name",), ("attributes", "quality", "updated"))
    return Node(
        name=as_text(f"{name}.name", mapping["name"]),
        attributes=frozenset(_texts(f"{name}.attributes", mapping.get("attributes", []))),
        quality=optional(as_fraction, f"{name}.quality", mapping.get("quality")),
        updated=optional(as_date, f"{name}.updated", mapping.get("updated")),
    )


def _edge(name: str, data: object) -> Edge:
    mapping = as_mapping(name, data)
    check_keys(name, mapping, ("source", "target", "transformation"))
    return Edge(as_text(f"{name}.source", mapping["source"]),
                as_text(f"{name}.target", mapping["target"]),
                as_text(f"{name}.transformation", mapping["transformation"]))


def _network(data: object) -> DataNetwork:
    mapping = as_mapping("network", data)
    check_keys("network", mapping, ("nodes",), ("edges",))
    nodes = [_node(f"network.nodes[{i}]", item)
             for i, item in enumerate(as_list("network.nodes", mapping["nodes"]))]
    edges = [_edge(f"network.edges[{i}]", item)
             for i, item in enumerate(as_list("network.edges", mapping.get("edges", [])))]
    return DataNetwork(tuple(nodes), tuple(edges))


def _meaning(data: object) -> Meaning:
    mapping = as_mapping("product.meaning", data)
    check_keys("product.meaning", mapping, ("definitions",), ("synonyms", "rules"))
    return Meaning(
        definitions=_text_map("product.meaning.definitions", mapping["definitions"]),
        synonyms=_text_map("product.meaning.synonyms", mapping.get("synonyms", {})),
        rules=_texts("product.meaning.rules", mapping.get("rules", [])),
    )


def _label(data: object) -> Label:
    mapping = as_mapping("product.label", data)
    check_keys("product.label", mapping, ("owner", "version", "frequency_days"), ("quality",))
    return Label(
        owner=as_text("product.label.owner", mapping["owner"]),
        version=as_text("product.label.version", mapping["version"]),
        frequency_days=as_int("product.label.frequency_days", mapping["frequency_days"]),
        quality=optional(as_fraction, "product.label.quality", mapping.get("quality")),
    )


def _links(data: object) -> Tuple[Tuple[str, str], ...]:
    links = []
    for i, item in enumerate(as_list("product.required_links", data)):
        pair = _texts(f"product.required_links[{i}]", item)
        if len(pair) != 2:
            raise ValueError(f"product.required_links[{i}] muss genau zwei Knoten nennen")
        links.append((pair[0], pair[1]))
    return tuple(links)


def _product(data: object, network: DataNetwork) -> Tuple[DataProduct, Tuple[Tuple[str, str], ...],
                                                        Tuple[str, ...]]:
    mapping = as_mapping("product", data)
    check_keys("product", mapping, ("name", "nodes", "meaning", "label"),
               ("edges", "required_links", "kpis"))
    edges = [_edge(f"product.edges[{i}]", item)
             for i, item in enumerate(as_list("product.edges", mapping.get("edges", [])))]
    product = DataProduct(
        name=as_text("product.name", mapping["name"]),
        network=network,
        node_names=frozenset(_texts("product.nodes", mapping["nodes"])),
        edges=tuple(edges),
        meaning=_meaning(mapping["meaning"]),
        label=_label(mapping["label"]),
    )
    return product, _links(mapping.get("required_links", [])), _texts("product.kpis", mapping.get("kpis", []))


def _accountabilities(data: object) -> Accountabilities:
    mapping = as_mapping("accountabilities", data)
    roles = ("data_owner", "data_product_owner", "use_case_owner")
    check_keys("accountabilities", mapping, (), roles)
    return Accountabilities(**{role: optional(as_text, f"accountabilities.{role}", mapping.get(role))
                               for role in roles})


def _level(name: str, value: object) -> ReliabilityLevel:
    if isinstance(value, bool):
        raise ValueError(f"{name} muss eine Stufe sein")
    if isinstance(value, int):
        try:
            return ReliabilityLevel(value)
        except ValueError:
            raise ValueError(f"{name}: Stufe muss 1 bis 4 sein, nicht {value}") from None
    if isinstance(value, str):
        if value in ReliabilityLevel.__members__:
            return ReliabilityLevel[value]
        raise ValueError(f"{name}: Unbekannte Stufe {value!r}")
    raise ValueError(f"{name} muss eine Stufe sein")


def _budget(name: str, data: object) -> ErrorBudget:
    mapping = as_mapping(name, data)
    check_keys(name, mapping, ("stakes", "epsilon"))
    return ErrorBudget(as_fraction(f"{name}.stakes", mapping["stakes"]),
                       as_fraction(f"{name}.epsilon", mapping["epsilon"]))


def _unit(name: str, value: object) -> Fraction:
    return unit_fraction(name, as_fraction(name, value))


def _case(name: str, data: object) -> ReferenceCase:
    mapping = as_mapping(name, data)
    check_keys(name, mapping, ("question", "reference", "tolerance"), ("weight",))
    return ReferenceCase(
        question=as_text(f"{name}.question", mapping["question"]),
        reference=as_fraction(f"{name}.reference", mapping["reference"]),
        tolerance=as_fraction(f"{name}.tolerance", mapping["tolerance"]),
        weight=as_fraction(f"{name}.weight", mapping.get("weight", 1)),
    )


def _use_case(data: object) -> UseCase:
    mapping = as_mapping("use_case", data)
    check_keys("use_case", mapping, ("level",), ("error_budget", "reference_cases", "min_pass_rate"))
    cases = tuple(_case(f"use_case.reference_cases[{i}]", item) for i, item in
                  enumerate(as_list("use_case.reference_cases", mapping.get("reference_cases", []))))
    questions = [case.question for case in cases]
    if len(set(questions)) != len(questions):
        raise ValueError("Fragen der Referenzfälle müssen eindeutig sein")
    if cases and sum((case.weight for case in cases), Fraction(0)) == 0:
        raise ValueError("Die Summe der Gewichte der Referenzfälle muss positiv sein")
    return UseCase(
        level=_level("use_case.level", mapping["level"]),
        budget=optional(_budget, "use_case.error_budget", mapping.get("error_budget")),
        cases=cases,
        min_pass_rate=optional(_unit, "use_case.min_pass_rate", mapping.get("min_pass_rate")),
    )


def _declared(data: object) -> Evidence:
    mapping = as_mapping("evidence", data)
    measured = [key for key in MEASURED if key in mapping]
    if measured:
        raise ValueError("evidence: wird aus den Daten gemessen und darf nicht erklärt werden: "
                         + ", ".join(measured))
    check_keys("evidence", mapping, (), ORGANIZATIONAL)
    return Evidence(**{key: as_bool(f"evidence.{key}", mapping.get(key, False)) for key in ORGANIZATIONAL})


def parse_spec(data: Mapping[str, object]) -> Spec:
    """Liest eine Spezifikation aus einem Mapping; ungültige oder unbekannte Angaben: ``ValueError``."""
    top = as_mapping("Spezifikation", data)
    check_keys("Spezifikation", top, ("network", "product", "use_case"), ("accountabilities", "evidence"))
    product, required_links, kpis = _product(top["product"], _network(top["network"]))
    return Spec(
        product=product,
        required_links=required_links,
        kpis=kpis,
        accountabilities=_accountabilities(top.get("accountabilities", {})),
        use_case=_use_case(top["use_case"]),
        declared=_declared(top.get("evidence", {})),
        raw=top,
    )


def load_spec(path: Union[str, Path]) -> Spec:
    """Liest und prüft eine Spezifikationsdatei (``.json``, ``.yaml``, ``.yml``)."""
    return parse_spec(read_document(path))


def _provenance(name: str, data: object) -> Provenance:
    mapping = as_mapping(name, data)
    check_keys(name, mapping, (), ("sources", "cutoff", "rules"))
    sources = []
    for i, item in enumerate(as_list(f"{name}.sources", mapping.get("sources", []))):
        pair = _texts(f"{name}.sources[{i}]", item)
        if len(pair) != 2:
            raise ValueError(f"{name}.sources[{i}] muss [Quelle, Version] sein")
        sources.append((pair[0], pair[1]))
    return Provenance(sources=tuple(sources),
                      cutoff=optional(as_date, f"{name}.cutoff", mapping.get("cutoff")),
                      rules=_texts(f"{name}.rules", mapping.get("rules", [])))


def parse_answers(data: Mapping[str, object]) -> Dict[str, Answer]:
    """Antworten je Frage: ``{Frage: {"value": Zahl|null, "provenance": {...}}}``."""
    answers: Dict[str, Answer] = {}
    for key, entry in as_mapping("Antworten", data).items():
        question = as_text("Frage", key)
        name = f"Antwort zu {question!r}"
        mapping = as_mapping(name, entry)
        check_keys(name, mapping, ("value",), ("provenance",))
        answers[question] = Answer(optional(as_fraction, f"{name}.value", mapping["value"]),
                                   optional(_provenance, f"{name}.provenance", mapping.get("provenance")))
    return answers


def answers_for(spec: Spec, data: Mapping[str, object]) -> Tuple[Answer, ...]:
    """Antworten in der Reihenfolge der Referenzfälle; fehlende Fragen gelten als unbeantwortet.

    Antworten zu Fragen, die kein Referenzfall kennt (Tippfehler), sind ein Fehler.
    """
    parsed = parse_answers(data)
    unknown = sorted(set(parsed) - {case.question for case in spec.use_case.cases})
    if unknown:
        raise ValueError(f"Antworten zu unbekannten Fragen: {', '.join(unknown)}")
    return collect_answers(spec.use_case.cases, StaticProvider(parsed))
