"""Kennzahlen zur Beobachtung von Reife und Nutzen (Abschnitt „Fortschritt messen").

Bestehensquote, erklärter Anteil, Provenance-Abdeckung, Vollständigkeit und Aktualität messen
verschiedene Eigenschaften und werden getrennt ausgewiesen, nie zu einer „KI-Genauigkeit"
zusammengefasst. Fehlende Antworten, unbekannte Aktualität und fehlende Provenance zählen
als nicht erfüllt, nie als Erfolg.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Iterable, Mapping, Optional, Sequence

from subgraph_sat_solver_econ.welfare import Rational, computation_gap, total_output

from .model import Answer, to_fraction, unit_fraction


@dataclass(frozen=True)
class ReferenceCase:
    """Testfall ``(q_j, y_j*)`` mit Toleranz ``δ_j`` und ökonomischem Gewicht ``w_j``."""

    question: str
    reference: Fraction
    tolerance: Fraction
    weight: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("Frage darf nicht leer sein")
        object.__setattr__(self, "reference", to_fraction(self.reference))
        object.__setattr__(self, "tolerance", to_fraction(self.tolerance))
        object.__setattr__(self, "weight", to_fraction(self.weight))
        if self.tolerance < 0 or self.weight < 0:
            raise ValueError("Toleranz und Gewicht müssen nichtnegativ sein")

    def passed(self, answer: Answer) -> bool:
        """``|ŷ − y*| ≤ δ``; ohne Antwort ist der Test nicht bestanden."""
        return answer.value is not None and abs(answer.value - self.reference) <= self.tolerance


def weighted_pass_rate(cases: Sequence[ReferenceCase], answers: Sequence[Answer]) -> Fraction:
    """Gewichtete Bestehensquote ``Σ w_j·1[|ŷ_j − y_j*| ≤ δ_j] / Σ w_j``."""
    if len(cases) != len(answers):
        raise ValueError("Testfälle und Antworten müssen gleich viele sein")
    weights = sum((case.weight for case in cases), Fraction(0))
    if weights == 0:
        raise ValueError("Die Summe der Gewichte muss positiv sein")
    passed = sum((case.weight for case, answer in zip(cases, answers) if case.passed(answer)), Fraction(0))
    return passed / weights


def provenance_coverage(answers: Sequence[Answer]) -> Fraction:
    """Anteil der Antworten mit vollständiger Provenance (Definition, Quelle, Datenstichtag)."""
    if not answers:
        raise ValueError("Mindestens eine Antwort erforderlich")
    complete = sum(1 for answer in answers if answer.provenance is not None and answer.provenance.is_complete())
    return Fraction(complete, len(answers))


@dataclass(frozen=True)
class Cause:
    """Ursache eines bekannten Effekts; ``explained`` ist der von der KI erklärte Anteil in ``[0, 1]``."""

    name: str
    amount: Fraction
    explained: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", to_fraction(self.amount))
        if self.amount < 0:
            raise ValueError("Betrag einer Ursache muss nichtnegativ sein")
        object.__setattr__(self, "explained", unit_fraction("Erklärter Anteil", self.explained))


def explained_share(causes: Sequence[Cause], total_effect: Optional[Rational] = None) -> Fraction:
    """Erklärter Anteil am bekannten Gesamteffekt.

    Formal identisch zur Rechenlücke des Referenzprojekts: erklärter Anteil ``= 1 − g`` mit
    ``g = (opt − A)/opt``, wobei ``opt`` der Gesamteffekt und ``A = Σ Betrag·erklärter Anteil`` ist.
    Ohne ``total_effect`` ist der Gesamteffekt die Summe der Ursachen; ein größerer Wert lässt einen
    nicht zugeordneten Rest unerklärt. Ein Gesamteffekt von 0 oder kleiner als die erklärte Summe ist ein Fehler.
    """
    explained_amount = total_output(
        [cause.amount for cause in causes], [1 - cause.explained for cause in causes]
    )
    total = sum((cause.amount for cause in causes), Fraction(0)) if total_effect is None \
        else to_fraction(total_effect)
    return 1 - computation_gap(total, explained_amount)


def attribute_completeness(rows: Iterable[Mapping[str, object]], attribute: str) -> Fraction:
    """Belegungsgrad eines kritischen Attributs; ``None`` und leere Texte gelten als nicht belegt."""
    rows = list(rows)
    if not rows:
        raise ValueError("Mindestens eine Zeile erforderlich")
    filled = 0
    for row in rows:
        value = row.get(attribute)
        if value is not None and not (isinstance(value, str) and not value.strip()):
            filled += 1
    return Fraction(filled, len(rows))


def is_fresh(updated: Optional[date], frequency_days: int, today: date) -> bool:
    """Aktualität: letzte Aktualisierung liegt höchstens ``frequency_days`` zurück; unbekannt gilt als nicht aktuell."""
    if frequency_days <= 0:
        raise ValueError("frequency_days muss positiv sein")
    return updated is not None and 0 <= (today - updated).days <= frequency_days


@dataclass(frozen=True)
class Evaluation:
    """Getrennte Kennzahlen eines Testlaufs; ohne Gesamtnote."""

    pass_rate: Fraction
    provenance_coverage: Fraction
    unanswered: int


def evaluate(cases: Sequence[ReferenceCase], answers: Sequence[Answer]) -> Evaluation:
    """Wertet Antworten gegen Testfälle aus und weist die Kennzahlen getrennt aus."""
    return Evaluation(
        pass_rate=weighted_pass_rate(cases, answers),
        provenance_coverage=provenance_coverage(answers),
        unanswered=sum(1 for answer in answers if answer.value is None),
    )
