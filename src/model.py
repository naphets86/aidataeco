"""Formales Modell des Datennetzes (Abschnitt „Formales Modell des Datennetzes").

Typisierte Schnittstellen für Daten-Netzwerk, Data Product, Label und Provenance. Leitplanken
der Arbeit: Verantwortliche werden nie implizit vorbelegt, und unbekannte Qualität, Aktualität
oder Provenance wird als ``None`` ausgewiesen statt als Erfolg gewertet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from fractions import Fraction
from typing import Dict, FrozenSet, Iterable, Mapping, Optional, Tuple

from subgraph_sat_solver_econ.welfare import Rational


def to_fraction(value: Rational) -> Fraction:
    """Exakte Zahl; Gleitkommawerte werden über ihre Dezimaldarstellung gelesen (``0.1`` → ``1/10``)."""
    if isinstance(value, float):
        return Fraction(repr(value))
    return Fraction(value)


def unit_fraction(name: str, value: Rational) -> Fraction:
    """Wert in ``[0, 1]`` (Qualität ``q_v``, Anteile); sonst ``ValueError``."""
    result = to_fraction(value)
    if not 0 <= result <= 1:
        raise ValueError(f"{name} muss in [0, 1] liegen")
    return result


def _required_text(name: str, value: Optional[str]) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{name} darf nicht leer sein")
    return value.strip()


@dataclass(frozen=True)
class Node:
    """Knoten ``v``: Tabelle, Datensatz oder Dokument mit Attributen ``A_v``.

    ``quality`` (``q_v ∈ [0,1]``) und ``updated`` (letzte Aktualisierung ``t_v``) sind
    ``None``, solange sie unbekannt sind.
    """

    name: str
    attributes: FrozenSet[str] = frozenset()
    quality: Optional[Fraction] = None
    updated: Optional[date] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text("Knotenname", self.name))
        object.__setattr__(self, "attributes", frozenset(self.attributes))
        if self.quality is not None:
            object.__setattr__(self, "quality", unit_fraction("Qualität", self.quality))


@dataclass(frozen=True)
class Edge:
    """Kante ``(u → v, φ)``: Join, Mapping oder Transformation ``φ`` zwischen zwei Knoten."""

    source: str
    target: str
    transformation: str


@dataclass(frozen=True)
class DataNetwork:
    """Gerichteter Multigraph ``G = (V, E)``; parallele Kanten sind erlaubt."""

    nodes: Tuple[Node, ...]
    edges: Tuple[Edge, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))
        names = [node.name for node in self.nodes]
        if len(set(names)) != len(names):
            raise ValueError("Knotennamen müssen eindeutig sein")
        for edge in self.edges:
            for end in (edge.source, edge.target):
                if end not in names:
                    raise ValueError(f"Kante verweist auf unbekannten Knoten {end!r}")

    def node(self, name: str) -> Node:
        for node in self.nodes:
            if node.name == name:
                return node
        raise ValueError(f"Unbekannter Knoten {name!r}")


@dataclass(frozen=True)
class Meaning:
    """Semantische Beschreibung ``𝓜``: Definitionen, Synonyme und Regeln."""

    definitions: Mapping[str, str]
    synonyms: Mapping[str, str] = field(default_factory=dict)
    rules: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "synonyms", dict(self.synonyms))
        object.__setattr__(self, "rules", tuple(self.rules))

    def resolve(self, term: str) -> str:
        """Definition eines Begriffs (auch über ein Synonym); ohne Definition ``ValueError``."""
        canonical = self.synonyms.get(term, term)
        if canonical not in self.definitions:
            raise ValueError(f"Begriff {term!r} ist nicht definiert")
        return self.definitions[canonical]


@dataclass(frozen=True)
class Label:
    """Label ``ℓ``: Owner, Qualität, Aktualisierungsfrequenz (Tage) und Version.

    Der Owner ist Pflicht; es gibt bewusst keinen Standardwert.
    """

    owner: str
    version: str
    frequency_days: int
    quality: Optional[Fraction] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner", _required_text("Owner", self.owner))
        object.__setattr__(self, "version", _required_text("Version", self.version))
        if self.frequency_days <= 0:
            raise ValueError("frequency_days muss positiv sein")
        if self.quality is not None:
            object.__setattr__(self, "quality", unit_fraction("Qualität", self.quality))


@dataclass(frozen=True)
class DataProduct:
    """Data Product ``P = (V_P, E_P, 𝓜, ℓ)`` als Teilnetz von ``G``."""

    name: str
    network: DataNetwork
    node_names: FrozenSet[str]
    edges: Tuple[Edge, ...]
    meaning: Meaning
    label: Label

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_text("Name des Data Products", self.name))
        object.__setattr__(self, "node_names", frozenset(self.node_names))
        object.__setattr__(self, "edges", tuple(self.edges))
        known = {node.name for node in self.network.nodes}
        if not self.node_names <= known:
            raise ValueError("V_P muss eine Teilmenge von V sein")
        for edge in self.edges:
            if edge not in self.network.edges:
                raise ValueError("E_P muss eine Teilmenge von E sein")
            if edge.source not in self.node_names or edge.target not in self.node_names:
                raise ValueError("Kanten von P dürfen nur Knoten von P verbinden")

    def missing_links(self, required: Iterable[Tuple[str, str]]) -> Tuple[Tuple[str, str], ...]:
        """Geforderte Verknüpfungen, die innerhalb von ``P`` nicht nachweisbar sind.

        Zwei Knoten gelten als verbunden, wenn ein Kantenzug in ``E_P`` (Richtung ignoriert)
        sie verbindet. Fehlt ein Knoten in ``V_P``, ist die Verknüpfung ebenfalls offen.
        """
        neighbours: Dict[str, set] = {name: set() for name in self.node_names}
        for edge in self.edges:
            neighbours[edge.source].add(edge.target)
            neighbours[edge.target].add(edge.source)
        missing = []
        for start, goal in required:
            if start not in neighbours or goal not in neighbours:
                missing.append((start, goal))
                continue
            reached = [start]  # Breitensuche; die Liste wächst während der Iteration
            for node in reached:
                reached.extend(sorted(neighbours[node].difference(reached)))
            if goal not in reached:
                missing.append((start, goal))
        return tuple(missing)

    def is_closed(self, required: Iterable[Tuple[str, str]]) -> bool:
        """``P`` ist geschlossen, wenn alle geforderten Verknüpfungen nachweisbar sind."""
        return not self.missing_links(required)


@dataclass(frozen=True)
class Provenance:
    """Provenance ``Π(ŷ)``: Quellen mit Version, Datenstichtag und angewendete Regeln."""

    sources: Tuple[Tuple[str, str], ...] = ()
    cutoff: Optional[date] = None
    rules: Tuple[str, ...] = ()

    def missing(self) -> Tuple[str, ...]:
        """Fehlende Bestandteile: ``Quelle``, ``Datenstichtag``, ``Definition``."""
        gaps = []
        if not self.sources:
            gaps.append("Quelle")
        if self.cutoff is None:
            gaps.append("Datenstichtag")
        if not self.rules:
            gaps.append("Definition")
        return tuple(gaps)

    def is_complete(self) -> bool:
        return not self.missing()


@dataclass(frozen=True)
class Answer:
    """Antwort ``ŷ`` einer KI-Anwendung. ``value=None``: es liegt keine Antwort vor."""

    value: Optional[Fraction]
    provenance: Optional[Provenance] = None

    def __post_init__(self) -> None:
        if self.value is not None:
            object.__setattr__(self, "value", to_fraction(self.value))

