"""Auswahl von Datenquellen als wirtschaftliches Optimierungsproblem.

Verallgemeinert die VOI-Bedingung der Arbeit (``E[ΔW] ≥ C_int`` je Quelle) auf mehrere Quellen mit
gemeinsamem Budget und Abhängigkeiten (eine Quelle braucht z. B. die Verknüpfung einer anderen). Das
ist eine Erweiterung des Modells, kein Satz der Arbeit.

Gelöst wird mit dem Solver des Referenzprojekts: ``Problem``, ``maximize`` und die Schaltkreisbausteine
stammen aus ``subgraph_sat_solver_econ``; hier wird nur das Problem formuliert.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from subgraph_sat_solver_econ.backends import BackendError, DpllBackend, SatBackend
from subgraph_sat_solver_econ.foundation import Problem, maximize


@dataclass(frozen=True)
class IntegrationOption:
    """Mögliche Integration: erwarteter Zusatznutzen ``E[ΔW]``, Kosten ``C_int`` (ganzzahlige Einheiten,
    z. B. T€) und Quellen, die dafür ebenfalls integriert sein müssen."""

    name: str
    gain: int
    cost: int
    requires: Tuple[str, ...] = ()


@dataclass(frozen=True)
class IntegrationPlan:
    """Optimale Auswahl: gewählte Quellen, Nettonutzen ``Σ(gain − cost)``, Gesamtkosten, Entscheideraufrufe."""

    selected: Tuple[str, ...]
    net_value: int
    total_cost: int
    calls: int


def _check(options: Sequence[IntegrationOption], budget: Optional[int]) -> None:
    names = [option.name for option in options]
    if len(set(names)) != len(names):
        raise ValueError("Namen der Optionen müssen eindeutig sein")
    for option in options:
        if option.gain < 0 or option.cost < 0:
            raise ValueError(f"Nutzen und Kosten von {option.name!r} müssen nichtnegativ sein")
        for required in option.requires:
            if required not in names:
                raise ValueError(f"{option.name!r} benötigt unbekannte Option {required!r}")
    if budget is not None and budget < 0:
        raise ValueError("Budget muss nichtnegativ sein")


def select_integrations(options: Sequence[IntegrationOption], budget: Optional[int] = None,
                        backend: Optional[SatBackend] = None) -> IntegrationPlan:
    """Wählt die Quellen mit maximalem Nettonutzen unter Budget und Abhängigkeiten.

    Kodierung: Bit ``x_i`` = „Quelle ``i`` wird integriert". Abhängigkeiten sind Klauseln
    ``(¬x_i ∨ x_r)``, das Budget ein Vergleicher auf der Kostensumme. Maximiert wird
    ``Σ gain_i·x_i + Σ cost_i·¬x_i``; abzüglich ``Σ cost_i`` ist das der Nettonutzen. Die Leere Auswahl
    ist immer zulässig, der Nettonutzen also nie negativ.
    """
    _check(options, budget)
    if not options:
        return IntegrationPlan((), 0, 0, 0)
    problem = Problem(len(options))
    index = {option.name: x for option, x in zip(options, problem.x)}
    for option, x in zip(options, problem.x):
        for required in option.requires:
            problem.cnf.add_clause(-x, index[required])
    cb = problem.cb
    if budget is not None:
        spent = cb.weighted_sum(problem.x, [option.cost for option in options])
        problem.require(cb.le_const(spent, budget))
    objective = cb.weighted_sum(
        list(problem.x) + [cb.neg(x) for x in problem.x],
        [option.gain for option in options] + [option.cost for option in options],
    )
    result = maximize(problem, objective, backend if backend is not None else DpllBackend())
    if not result.feasible or result.value is None or result.x is None:  # pragma: no cover
        raise BackendError("Die leere Auswahl ist zulässig; der Entscheider antwortet widersprüchlich")
    chosen = [option for option, picked in zip(options, result.x) if picked]
    base = sum(option.cost for option in options)
    return IntegrationPlan(
        selected=tuple(option.name for option in chosen),
        net_value=result.value - base,
        total_cost=sum(option.cost for option in chosen),
        calls=result.calls,
    )
