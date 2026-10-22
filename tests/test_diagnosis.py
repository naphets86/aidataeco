from fractions import Fraction

import pytest

from src.diagnosis import (
    Deviation,
    DeviationCause,
    bayes_update,
    expected_gain,
    integration_rational,
    posterior_odds,
    posterior_probability,
    processed_deviations,
)


def test_posterior_odds_multiply_prior_odds_and_likelihood_ratio():
    assert posterior_odds(Fraction(1, 4), Fraction(3, 5), Fraction(1, 5)) == 1
    assert posterior_odds(Fraction(1, 2), Fraction(1, 10), Fraction(1, 5)) == Fraction(1, 2)


def test_posterior_probability_rises_when_deviation_is_likelier_under_h1():
    prior = Fraction(1, 10)
    assert posterior_probability(prior, Fraction(8, 10), Fraction(2, 10)) > prior
    assert posterior_probability(prior, Fraction(1, 10), Fraction(2, 10)) < prior
    assert posterior_probability(Fraction(1, 2), 1, 1) == Fraction(1, 2)
    assert posterior_probability(Fraction(1, 2), 0, 1) == 0


def test_posterior_odds_reject_undefined_inputs():
    with pytest.raises(ValueError, match="Prior"):
        posterior_odds(0, 1, 1)
    with pytest.raises(ValueError, match="Prior"):
        posterior_odds(1, 1, 1)
    with pytest.raises(ValueError, match="nichtnegativ"):
        posterior_odds(0.5, -1, 1)
    with pytest.raises(ValueError, match="nichtnegativ"):
        posterior_odds(0.5, 1, -1)
    with pytest.raises(ValueError, match="undefiniert"):
        posterior_odds(0.5, 1, 0)


def test_bayes_update_normalizes_the_posterior():
    prior = {"verknüpft": Fraction(7, 10), "lücke": Fraction(3, 10)}
    likelihood = {"verknüpft": Fraction(1, 10), "lücke": Fraction(6, 10)}
    posterior = bayes_update(prior, likelihood)
    assert posterior == {"verknüpft": Fraction(7, 25), "lücke": Fraction(18, 25)}
    assert sum(posterior.values()) == 1


def test_bayes_update_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="dieselben Zustände"):
        bayes_update({"a": 1}, {"b": 1})
    with pytest.raises(ValueError, match="summieren"):
        bayes_update({"a": 0.5}, {"a": 1})
    with pytest.raises(ValueError, match="nichtnegativ sein und sich"):
        bayes_update({"a": 2, "b": -1}, {"a": 1, "b": 1})
    with pytest.raises(ValueError, match="Likelihoods"):
        bayes_update({"a": 1}, {"a": -1})
    with pytest.raises(ValueError, match="Wahrscheinlichkeit 0"):
        bayes_update({"a": 1}, {"a": 0})


def test_expected_gain_and_voi_condition():
    posterior = {"fehlt": Fraction(3, 4), "vorhanden": Fraction(1, 4)}
    gain = expected_gain(posterior, {"fehlt": 200, "vorhanden": 0})
    assert gain == 150
    assert integration_rational(gain, 150)
    assert integration_rational(gain, 100)
    assert not integration_rational(gain, 151)
    with pytest.raises(ValueError, match="dieselben Zustände"):
        expected_gain({"a": 1}, {"b": 1})
    with pytest.raises(ValueError, match="nichtnegativ"):
        integration_rational(1, -1)


def test_every_cause_has_a_response():
    assert len(DeviationCause) == 5
    for cause in DeviationCause:
        assert cause.response.endswith(".")
    assert "Quelle" in DeviationCause.MISSING_SOURCE.response
    assert "interne Analyse" in DeviationCause.INCOMPLETE_OWN_ANALYSIS.response


def test_deviations_count_as_processed_only_with_documented_outcome():
    deviations = [
        Deviation(DeviationCause.MISSING_SOURCE, "Fracht mit Aufträgen verknüpft"),
        Deviation(DeviationCause.STALE_DATA),
        Deviation(DeviationCause.UNCLEAR_DEFINITION, "   "),
        Deviation(DeviationCause.INCOMPLETE_OWN_ANALYSIS, "Controlling-Analyse ergänzt"),
    ]
    assert [d.processed for d in deviations] == [True, False, False, True]
    assert processed_deviations(deviations) == 2
    assert processed_deviations([]) == 0
