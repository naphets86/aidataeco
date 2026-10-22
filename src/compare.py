"""Vergleich zweier Freigabeberichte über die Zeit (Abschnitt „Operationalisierung").

Jede Kennzahl hat eine Richtung (höher oder niedriger ist besser). Fehlender Nachweis (``None``)
gilt als schlechter als jeder belegte Wert. Verglichen wird exakt, ohne Rundung oder Toleranz.
Eine *Regression* liegt vor, wenn sich mindestens eine Kennzahl verschlechtert oder ein Freigabe-
hindernis neu hinzukommt.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional, Tuple

from .experiment import canonical_json
from .governance import ReliabilityLevel
from .report import GoLiveReport



class Direction(Enum):
    IMPROVED = "verbessert"
    UNCHANGED = "unverändert"
    REGRESSED = "verschlechtert"


def direction(before: Optional[object], after: Optional[object], higher_is_better: bool) -> Direction:
    """Richtung einer Änderung; ``None`` (kein Nachweis) ist schlechter als jeder Wert."""
    if before == after:
        return Direction.UNCHANGED
    if after is None:
        return Direction.REGRESSED
    if before is None:
        return Direction.IMPROVED
    better = after > before if higher_is_better else after < before
    return Direction.IMPROVED if better else Direction.REGRESSED


@dataclass(frozen=True)
class Change:
    metric: str
    before: Optional[object]
    after: Optional[object]
    direction: Direction


def _evaluated(report: GoLiveReport, pick: Callable) -> Optional[object]:
    return None if report.evaluation is None else pick(report.evaluation)


_METRICS: Tuple[Tuple[str, Callable[[GoLiveReport], Optional[object]], bool], ...] = (
    ("Bestehensquote", lambda r: _evaluated(r, lambda e: e.pass_rate), True),
    ("Provenance-Abdeckung", lambda r: _evaluated(r, lambda e: e.provenance_coverage), True),
    ("Unbeantwortete Fragen", lambda r: _evaluated(r, lambda e: e.unanswered), False),
    ("Offene Verknüpfungen", lambda r: len(r.missing_links), False),
    ("Knoten ohne Aktualitätsnachweis", lambda r: sum(1 for n in r.nodes if n.fresh is not True), False),
    ("Knoten ohne bekannte Qualität", lambda r: sum(1 for n in r.nodes if n.quality is None), False),
    ("Freigabehindernisse", lambda r: len(r.blockers), False),
)


@dataclass(frozen=True)
class Comparison:
    """Ergebnis des Vergleichs ``alt → neu``."""

    product: str
    version_before: str
    version_after: str
    level_before: ReliabilityLevel
    level_after: ReliabilityLevel
    fingerprint_changed: bool
    changes: Tuple[Change, ...]
    new_blockers: Tuple[str, ...]
    resolved_blockers: Tuple[str, ...]

    @property
    def regressions(self) -> Tuple[Change, ...]:
        return tuple(change for change in self.changes if change.direction is Direction.REGRESSED)

    @property
    def has_regression(self) -> bool:
        return bool(self.regressions) or bool(self.new_blockers)

    def to_dict(self) -> Dict[str, object]:
        return {
            "product": self.product,
            "version_before": self.version_before,
            "version_after": self.version_after,
            "level_before": self.level_before.name,
            "level_after": self.level_after.name,
            "fingerprint_changed": self.fingerprint_changed,
            "changes": [{"metric": c.metric,
                         "before": None if c.before is None else str(c.before),
                         "after": None if c.after is None else str(c.after),
                         "direction": c.direction.name} for c in self.changes],
            "new_blockers": list(self.new_blockers),
            "resolved_blockers": list(self.resolved_blockers),
            "has_regression": self.has_regression,
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict()) + "\n"

    def to_markdown(self) -> str:
        verdict = "**Regression festgestellt.**" if self.has_regression else "Keine Regression."
        lines = [
            f"# Vergleich: {self.product}",
            "",
            f"- Version: {self.version_before} → {self.version_after}",
            f"- Stufe: {self.level_before.name} → {self.level_after.name}",
            f"- Eingaben geändert: {'ja' if self.fingerprint_changed else 'nein'}",
            "",
            verdict,
            "",
            "| Kennzahl | Vorher | Nachher | Richtung |",
            "|---|---|---|---|",
        ]
        for change in self.changes:
            before = "nicht belegt" if change.before is None else str(change.before)
            after = "nicht belegt" if change.after is None else str(change.after)
            lines.append(f"| {change.metric} | {before} | {after} | {change.direction.value} |")
        if self.new_blockers:
            lines += ["", "## Neue Freigabehindernisse", ""] + [f"- {b}" for b in self.new_blockers]
        if self.resolved_blockers:
            lines += ["", "## Behobene Freigabehindernisse", ""] + [f"- {b}" for b in self.resolved_blockers]
        return "\n".join(lines) + "\n"


def compare_reports(old: GoLiveReport, new: GoLiveReport) -> Comparison:
    """Vergleicht zwei Berichte desselben Data Products (``old`` ist der frühere Stand)."""
    if old.product != new.product:
        raise ValueError("Berichte verschiedener Data Products sind nicht vergleichbar")
    changes = tuple(
        Change(metric, pick(old), pick(new), direction(pick(old), pick(new), higher))
        for metric, pick, higher in _METRICS
    )
    return Comparison(
        product=new.product,
        version_before=old.version, version_after=new.version,
        level_before=old.level, level_after=new.level,
        fingerprint_changed=old.fingerprint != new.fingerprint,
        changes=changes,
        new_blockers=tuple(sorted(set(new.blockers) - set(old.blockers))),
        resolved_blockers=tuple(sorted(set(old.blockers) - set(new.blockers))),
    )
