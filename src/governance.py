"""Vertrauensstufen, Verantwortlichkeiten und Freigabe (Abschnitte „Vertrauensstufen" und „Verantwortung und Freigabe").

Die Stufen sind ein konzeptioneller Rahmen, keine Norm. Fehlender Nachweis zählt nie als
erfüllt: jedes Beweisfeld in :class:`Evidence` ist standardmäßig ``False``. Ein Ergebnis dieses
Moduls ist keine automatische Freigabe, sondern die Liste dessen, was einer Freigabe noch im Weg steht.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple


class ReliabilityLevel(IntEnum):
    """Nutzungsstufen nach erforderlicher Zuverlässigkeit."""

    HINT = 1
    CROSS_CHECK = 2
    DECISION_PREPARATION = 3
    AUTOMATED_ACTION = 4


@dataclass(frozen=True)
class Accountabilities:
    """Die drei Verantwortlichkeiten vor dem Go-live. Rollen können dieselbe Person sein, müssen aber benannt sein."""

    data_owner: Optional[str] = None
    data_product_owner: Optional[str] = None
    use_case_owner: Optional[str] = None

    def missing(self) -> Tuple[str, ...]:
        """Namen der Rollen ohne benannte Person."""
        roles = (
            ("Data Owner", self.data_owner),
            ("Data Product Owner", self.data_product_owner),
            ("Use-Case Owner", self.use_case_owner),
        )
        return tuple(role for role, person in roles if person is None or not person.strip())


@dataclass(frozen=True)
class Evidence:
    """Nachweise für eine Freigabe; ``False`` heißt „nicht belegt"."""

    kpis_defined: bool = False
    provenance_available: bool = False
    quality_measurable: bool = False
    error_budget_met: bool = False
    human_decides: bool = False
    explicit_approval: bool = False
    logging: bool = False
    intervention_path: bool = False


_DESCRIPTIONS = {
    "kpis_defined": "Zentrale Kennzahlen sind verknüpft und definiert",
    "provenance_available": "Quelle, Definition und Zeitstempel sind verfügbar",
    "quality_measurable": "Qualität ist messbar",
    "error_budget_met": "Error Budget ist für den Anwendungsfall eingehalten",
    "explicit_approval": "Ausdrückliche Freigabe liegt vor",
    "logging": "Protokollierung ist eingerichtet",
    "intervention_path": "Eingriffspfad ist festgelegt",
}

# Anforderungen je Stufe; höhere Stufen schließen die Anforderungen der niedrigeren ein.
_REQUIRED = (
    (ReliabilityLevel.CROSS_CHECK, ("kpis_defined",)),
    (ReliabilityLevel.DECISION_PREPARATION,
     ("provenance_available", "quality_measurable", "error_budget_met")),
    (ReliabilityLevel.AUTOMATED_ACTION, ("explicit_approval", "logging", "intervention_path")),
)


def release_blockers(level: ReliabilityLevel, accountabilities: Accountabilities,
                     evidence: Evidence) -> List[str]:
    """Gründe, die eine Freigabe auf ``level`` verhindern; leere Liste: nichts steht im Weg.

    Fehlende Verantwortliche blockieren jede Stufe. Auf Stufe 3 muss zusätzlich ein Mensch
    entscheiden; auf Stufe 4 entfällt das, dafür sind Freigabe, Protokoll und Eingriffspfad nötig.
    """
    blockers = [f"Keine verantwortliche Person benannt: {role}" for role in accountabilities.missing()]
    for required_level, fields in _REQUIRED:
        if level >= required_level:
            blockers.extend(
                f"Nachweis fehlt: {_DESCRIPTIONS[name]}" for name in fields if not getattr(evidence, name)
            )
    if level == ReliabilityLevel.DECISION_PREPARATION and not evidence.human_decides:
        blockers.append("Nachweis fehlt: Ein Mensch entscheidet")
    return blockers
