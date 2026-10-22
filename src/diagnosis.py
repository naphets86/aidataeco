"""Abweichungen als diagnostisches Signal (Abschnitt „Abweichungen als Chance").

Bayes-Indikator, Lern-Loop-Update und VOI-Bedingung. Alle Rechnungen sind exakt
(:class:`fractions.Fraction`). Undefinierte Fälle (z. B. Likelihood 0 unter ``H_0``) lösen
``ValueError`` aus; sie werden nicht stillschweigend zu einer Zahl.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Dict, Iterable, Mapping, Optional

from subgraph_sat_solver_econ.welfare import Rational

from .model import to_fraction


def posterior_odds(prior_h1: Rational, likelihood_h1: Rational, likelihood_h0: Rational) -> Fraction:
    """Posterior Odds ``P(H1|d)/P(H0|d) = P(H1)/P(H0) · p(d|H1)/p(d|H0)``."""
    prior, l1, l0 = to_fraction(prior_h1), to_fraction(likelihood_h1), to_fraction(likelihood_h0)
    if not 0 < prior < 1:
        raise ValueError("Prior P(H1) muss in (0, 1) liegen")
    if l1 < 0 or l0 < 0:
        raise ValueError("Likelihoods müssen nichtnegativ sein")
    if l0 == 0:
        raise ValueError("p(d|H0) = 0: die Odds sind undefiniert")
    return prior / (1 - prior) * l1 / l0


def posterior_probability(prior_h1: Rational, likelihood_h1: Rational,
                          likelihood_h0: Rational) -> Fraction:
    """Posterior ``P(H1|d)`` aus den Odds."""
    odds = posterior_odds(prior_h1, likelihood_h1, likelihood_h0)
    return odds / (1 + odds)


def bayes_update(prior: Mapping[str, Rational], likelihood: Mapping[str, Rational]) -> Dict[str, Fraction]:
    """Lern-Loop: ``π₁(θ) ∝ p(d|θ)·π₀(θ)`` über einem endlichen Zustandsraum."""
    if set(prior) != set(likelihood):
        raise ValueError("Prior und Likelihood müssen dieselben Zustände haben")
    pi0 = {state: to_fraction(p) for state, p in prior.items()}
    if any(p < 0 for p in pi0.values()) or sum(pi0.values()) != 1:
        raise ValueError("Prior muss nichtnegativ sein und sich zu 1 summieren")
    lik = {state: to_fraction(p) for state, p in likelihood.items()}
    if any(p < 0 for p in lik.values()):
        raise ValueError("Likelihoods müssen nichtnegativ sein")
    evidence = sum(lik[s] * pi0[s] for s in pi0)
    if evidence == 0:
        raise ValueError("Die beobachtete Abweichung hat Wahrscheinlichkeit 0 unter dem Prior")
    return {s: lik[s] * pi0[s] / evidence for s in pi0}


def expected_gain(posterior: Mapping[str, Rational], gains: Mapping[str, Rational]) -> Fraction:
    """Erwarteter Zusatznutzen ``E_{π₁}[ΔW(θ)] = Σ_θ π₁(θ)·ΔW(θ)`` (Beweisskizze VOI)."""
    if set(posterior) != set(gains):
        raise ValueError("Posterior und Nutzen müssen dieselben Zustände haben")
    return sum((to_fraction(posterior[s]) * to_fraction(gains[s]) for s in posterior), Fraction(0))


def integration_rational(expected_gain_value: Rational, cost: Rational) -> bool:
    """VOI-Bedingung: Erweiterung ist rational genau dann, wenn ``E[ΔW] ≥ C_int``."""
    integration_cost = to_fraction(cost)
    if integration_cost < 0:
        raise ValueError("Integrationskosten müssen nichtnegativ sein")
    return to_fraction(expected_gain_value) >= integration_cost


class DeviationCause(Enum):
    """Mögliche Ursachen einer Abweichung mit der jeweils geeigneten Reaktion (Tabelle der Arbeit)."""

    MISSING_SOURCE = "Fehlende Datenquelle"
    MISSING_ATTRIBUTE = "Fehlendes Attribut"
    UNCLEAR_DEFINITION = "Unklare Definition"
    STALE_DATA = "Veraltete Daten"
    INCOMPLETE_OWN_ANALYSIS = "Unvollständige eigene Analyse"

    @property
    def response(self) -> str:
        return _RESPONSES[self]


_RESPONSES = {
    DeviationCause.MISSING_SOURCE: "Quelle mit dem Data Product verbinden und Zuständigkeit festlegen.",
    DeviationCause.MISSING_ATTRIBUTE: "Attribut ergänzen und dessen Vollständigkeit überwachen.",
    DeviationCause.UNCLEAR_DEFINITION: (
        "Data Owner legt Bedeutung fest und dokumentiert Synonyme und Geltungsbereich."),
    DeviationCause.STALE_DATA: "Aktualisierungsfrequenz klären und Datenstichtag ausweisen.",
    DeviationCause.INCOMPLETE_OWN_ANALYSIS: (
        "Hinweis prüfen und gegebenenfalls die interne Analyse korrigieren."),
}


@dataclass(frozen=True)
class Deviation:
    """Eine Abweichung zwischen KI-Antwort und interner Analyse.

    ``outcome`` hält die dokumentierte Korrektur oder die begründete Bestätigung fest;
    ``None`` bedeutet: noch nicht bearbeitet.
    """

    cause: DeviationCause
    outcome: Optional[str] = None

    @property
    def processed(self) -> bool:
        return bool(self.outcome and self.outcome.strip())


def processed_deviations(deviations: Iterable[Deviation]) -> int:
    """Kennzahl „Bearbeitete Abweichungen": Anzahl mit dokumentiertem Ergebnis."""
    return sum(1 for deviation in deviations if deviation.processed)
