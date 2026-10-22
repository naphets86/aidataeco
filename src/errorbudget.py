"""Fehlerzusammensetzung und Gut-genug-Bedingung (Abschnitt „Fehlerzusammensetzung und Gut genug").

Die Arbeit setzt **keinen** universellen Schwellenwert: Verlustfunktion, Stakes ``W`` und
Anteil ``ε`` müssen für jeden Anwendungsfall fachlich bestimmt und hier übergeben werden.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping

from subgraph_sat_solver_econ.welfare import Rational

from .model import to_fraction


@dataclass(frozen=True)
class ErrorBudget:
    """Error Budget: erwarteter Verlust darf höchstens ``ε·W`` betragen (``W ≥ 0``, ``ε > 0``)."""

    stakes: Fraction
    epsilon: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "stakes", to_fraction(self.stakes))
        object.__setattr__(self, "epsilon", to_fraction(self.epsilon))
        if self.stakes < 0:
            raise ValueError("Stakes W müssen nichtnegativ sein")
        if self.epsilon <= 0:
            raise ValueError("Error Budget ε muss positiv sein")

    @property
    def limit(self) -> Fraction:
        """Zulässiger erwarteter Verlust ``ε·W``."""
        return self.epsilon * self.stakes


def is_good_enough(expected_loss: Rational, budget: ErrorBudget) -> bool:
    """Ökonomische Gut-genug-Bedingung ``E[L(ŷ, y*)] ≤ ε·W``."""
    loss = to_fraction(expected_loss)
    if loss < 0:
        raise ValueError("Erwarteter Verlust muss nichtnegativ sein")
    return loss <= budget.limit


def linear_loss(cost_per_unit: Rational, expected_abs_error: Rational) -> Fraction:
    """Erwarteter Verlust bei linearem Loss ``L = c·|ŷ − y*|``, also ``c·E|B_miss + B_def + η|``."""
    cost, error = to_fraction(cost_per_unit), to_fraction(expected_abs_error)
    if cost < 0 or error < 0:
        raise ValueError("Kostensatz und erwarteter Fehlerbetrag müssen nichtnegativ sein")
    return cost * error


def good_enough_linear(cost_per_unit: Rational, expected_abs_error: Rational,
                       budget: ErrorBudget) -> bool:
    """Praktische Bedingung ``c·E|…| ≤ ε·W`` unter linearem Loss."""
    return is_good_enough(linear_loss(cost_per_unit, expected_abs_error), budget)


@dataclass(frozen=True)
class ErrorDecomposition:
    """Fehlerzerlegung ``ŷ − y* = B_miss + B_def + η`` (Satz „Fehlerzerlegung")."""

    b_miss: Fraction
    b_def: Fraction
    eta: Fraction

    def __post_init__(self) -> None:
        for name in ("b_miss", "b_def", "eta"):
            object.__setattr__(self, name, to_fraction(getattr(self, name)))

    @property
    def total(self) -> Fraction:
        """Antwortfehler ``ŷ − y*``."""
        return self.b_miss + self.b_def + self.eta

    @property
    def expected(self) -> Fraction:
        """``E[ŷ − y*] = B_miss + B_def`` (das Rauschen ``η`` hat Erwartungswert 0)."""
        return self.b_miss + self.b_def


def missing_bias(effects: Mapping[str, Rational], observed: Iterable[str]) -> Fraction:
    """Bias durch fehlende Einflussgrößen ``B_miss = −Σ_{i ∈ S_q∖S̃_q} α_i·s_i``.

    ``effects`` bildet jede wesentliche Einflussgröße ``i ∈ S_q`` auf ihren Beitrag
    ``α_i·s_i`` ab; ``observed`` ist die im Netz beobachtbare Teilmenge ``S̃_q``.
    """
    seen = set(observed)
    unknown = seen - set(effects)
    if unknown:
        raise ValueError(f"Beobachtete Größen nicht in S_q: {sorted(unknown)}")
    return -sum((to_fraction(v) for k, v in effects.items() if k not in seen), Fraction(0))


def lipschitz_bound(lipschitz: Rational, driver_distance: Rational, b_def: Rational,
                    eta: Rational) -> Fraction:
    """Schranke ``|ŷ − y*| ≤ L·‖S_q − S̃_q‖ + |B_def| + |η|`` (nichtlineare Erweiterung)."""
    const, distance = to_fraction(lipschitz), to_fraction(driver_distance)
    if const < 0 or distance < 0:
        raise ValueError("Lipschitz-Konstante und Abstand müssen nichtnegativ sein")
    return const * distance + abs(to_fraction(b_def)) + abs(to_fraction(eta))
