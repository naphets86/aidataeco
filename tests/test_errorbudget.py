from fractions import Fraction

import pytest

from src.errorbudget import (
    ErrorBudget,
    ErrorDecomposition,
    good_enough_linear,
    is_good_enough,
    linear_loss,
    lipschitz_bound,
    missing_bias,
)


def test_budget_limit_is_epsilon_times_stakes():
    budget = ErrorBudget(stakes=440, epsilon=0.05)
    assert budget.limit == Fraction(22)
    assert ErrorBudget(0, Fraction(1, 10)).limit == 0


def test_budget_rejects_invalid_parameters():
    with pytest.raises(ValueError, match="Stakes"):
        ErrorBudget(-1, 0.1)
    with pytest.raises(ValueError, match="ε"):
        ErrorBudget(1, 0)


def test_good_enough_is_inclusive_at_the_limit():
    budget = ErrorBudget(100, Fraction(1, 10))
    assert is_good_enough(10, budget)
    assert is_good_enough(Fraction(19, 2), budget)
    assert not is_good_enough(Fraction(101, 10), budget)
    with pytest.raises(ValueError, match="nichtnegativ"):
        is_good_enough(-1, budget)


def test_linear_loss_and_condition():
    budget = ErrorBudget(1000, Fraction(1, 100))
    assert linear_loss(2, Fraction(5)) == 10
    assert good_enough_linear(2, 5, budget)
    assert not good_enough_linear(3, 5, budget)
    with pytest.raises(ValueError, match="nichtnegativ"):
        linear_loss(-1, 1)
    with pytest.raises(ValueError, match="nichtnegativ"):
        linear_loss(1, -1)


def test_error_decomposition_adds_up_and_expectation_ignores_noise():
    parts = ErrorDecomposition(b_miss=-380, b_def=5, eta=Fraction(1, 2))
    assert parts.total == Fraction(-749, 2)
    assert parts.expected == -375
    assert ErrorDecomposition(0.5, 0, 0).b_miss == Fraction(1, 2)


def test_missing_bias_sums_only_unobserved_drivers():
    effects = {"Rabatt": 60, "Fracht": 230, "Produktgruppe": 150}
    assert missing_bias(effects, ["Rabatt"]) == -380
    assert missing_bias(effects, effects) == 0
    assert missing_bias(effects, []) == -440
    with pytest.raises(ValueError, match="nicht in S_q"):
        missing_bias(effects, ["Wetter"])


def test_lipschitz_bound_adds_all_terms():
    assert lipschitz_bound(2, 3, -1, Fraction(-1, 2)) == Fraction(15, 2)
    with pytest.raises(ValueError, match="nichtnegativ"):
        lipschitz_bound(-1, 1, 0, 0)
    with pytest.raises(ValueError, match="nichtnegativ"):
        lipschitz_bound(1, -1, 0, 0)
