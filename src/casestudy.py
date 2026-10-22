"""Illustrative Fallstudie „Warum sinkt die Marge?" (Maschinenbauzulieferer, Q1 bis Q3 2026).

Die Zahlen stammen aus der Arbeit, die sie auf ein Webinar zurückführt. Sie sind illustrativ und keine
unabhängig erhobenen Unternehmensdaten. Beträge in T€.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple

from subgraph_sat_solver_econ.welfare import Rational

from .evaluation import Cause, explained_share
from .model import to_fraction


def margin_gap(revenue: Rational, previous_margin: Rational, current_margin: Rational) -> Fraction:
    """Differenz zwischen dem DB II bei Vorjahresmarge und dem tatsächlichen DB II (auf aktuellen Umsatz)."""
    return to_fraction(revenue) * (to_fraction(previous_margin) - to_fraction(current_margin))


@dataclass(frozen=True)
class MarginCase:
    """Aufteilung der DB-II-Abweichung auf Ursachen."""

    revenue: Fraction
    previous_margin: Fraction
    current_margin: Fraction
    causes: Tuple[Cause, ...]

    def __post_init__(self) -> None:
        if sum((cause.amount for cause in self.causes), Fraction(0)) != self.gap:
            raise ValueError("Die Ursachen müssen die Abweichung genau aufteilen")

    @property
    def gap(self) -> Fraction:
        return margin_gap(self.revenue, self.previous_margin, self.current_margin)

    @property
    def expected_db2(self) -> Fraction:
        """DB II bei Vorjahresmarge."""
        return self.revenue * self.previous_margin

    @property
    def actual_db2(self) -> Fraction:
        return self.revenue * self.current_margin

    @property
    def explained_share(self) -> Fraction:
        """Von der KI erklärter Anteil der Abweichung (in der Arbeit etwa 14 %)."""
        return explained_share(self.causes, self.gap)


def margin_case() -> MarginCase:
    """Fallstudie der Arbeit: Umsatz 11,0 Mio. €, Marge 28 % → 24 %, Abweichung 440 T€."""
    return MarginCase(
        revenue=Fraction(11000),
        previous_margin=Fraction(28, 100),
        current_margin=Fraction(24, 100),
        causes=(
            Cause("Expressfracht", 230, 0),
            Cause("Produktmix", 150, 0),
            Cause("Rabatte", 60, 1),
        ),
    )
