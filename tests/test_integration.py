from itertools import product

import pytest
from subgraph_sat_solver_econ.backends import ChainBackend, CountingBackend, DpllBackend
from subgraph_sat_solver_econ.foundation import opt_call_bound

from src.diagnosis import integration_rational
from src.integration import IntegrationOption, select_integrations

CASE = [
    IntegrationOption("Fracht", 230, 40, ("Join",)),
    IntegrationOption("Join", 0, 20),
    IntegrationOption("Produktgruppe", 150, 60),
    IntegrationOption("Teuer", 50, 80),
]


def brute_force(options, budget):
    best = 0
    for picks in product((False, True), repeat=len(options)):
        chosen = {o.name for o, p in zip(options, picks) if p}
        if any(r not in chosen for o in options if o.name in chosen for r in o.requires):
            continue
        cost = sum(o.cost for o in options if o.name in chosen)
        if budget is not None and cost > budget:
            continue
        best = max(best, sum(o.gain - o.cost for o in options if o.name in chosen))
    return best


def test_selection_respects_dependencies_and_rejects_unprofitable_sources():
    plan = select_integrations(CASE)
    assert plan.selected == ("Fracht", "Join", "Produktgruppe")
    assert plan.net_value == 260
    assert plan.total_cost == 120
    assert "Teuer" not in plan.selected


def test_budget_changes_the_choice():
    plan = select_integrations(CASE, budget=70)
    assert plan.selected == ("Fracht", "Join")
    assert plan.net_value == 170
    assert plan.total_cost == 60
    assert select_integrations(CASE, budget=0).selected == ()
    assert select_integrations(CASE, budget=10_000).selected == ("Fracht", "Join", "Produktgruppe")


@pytest.mark.parametrize("budget", [None, 0, 25, 60, 100, 180, 500])
def test_selection_matches_brute_force(budget):
    assert select_integrations(CASE, budget).net_value == brute_force(CASE, budget)


def test_single_source_agrees_with_the_voi_condition():
    for gain, cost in [(100, 100), (99, 100), (101, 100), (0, 0)]:
        option = IntegrationOption("x", gain, cost)
        picked = bool(select_integrations([option]).selected)
        # Bei Gleichstand (Nettonutzen 0) wählt der Solver die leere Auswahl.
        assert picked == (integration_rational(gain, cost) and gain > cost)


def test_empty_and_zero_value_inputs():
    plan = select_integrations([])
    assert (plan.selected, plan.net_value, plan.total_cost, plan.calls) == ((), 0, 0, 0)
    assert select_integrations([IntegrationOption("gratis", 0, 0)]).net_value == 0


def test_solver_calls_stay_within_the_bound_of_the_paper():
    counter = CountingBackend(DpllBackend())
    plan = select_integrations(CASE, budget=70, backend=counter)
    assert plan.calls == counter.calls
    assert plan.calls <= opt_call_bound(width=12, n=len(CASE))


@pytest.mark.integration
@pytest.mark.slow
def test_python_reference_chain_gives_the_same_optimum():
    options = [IntegrationOption("a", 2, 1), IntegrationOption("b", 1, 0, ("a",))]
    assert select_integrations(options, backend=ChainBackend()) == select_integrations(options)


def test_invalid_options_are_rejected():
    with pytest.raises(ValueError, match="eindeutig"):
        select_integrations([IntegrationOption("a", 1, 1), IntegrationOption("a", 1, 1)])
    with pytest.raises(ValueError, match="nichtnegativ"):
        select_integrations([IntegrationOption("a", -1, 1)])
    with pytest.raises(ValueError, match="nichtnegativ"):
        select_integrations([IntegrationOption("a", 1, -1)])
    with pytest.raises(ValueError, match="unbekannte Option"):
        select_integrations([IntegrationOption("a", 1, 1, ("b",))])
    with pytest.raises(ValueError, match="Budget"):
        select_integrations([IntegrationOption("a", 1, 1)], budget=-1)
