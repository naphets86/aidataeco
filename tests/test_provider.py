from fractions import Fraction

import pytest

from src.evaluation import ReferenceCase
from src.model import Answer
from src.provider import ProviderError, StaticProvider, collect_answers

CASES = (ReferenceCase("a", 1, 0), ReferenceCase("b", 2, 0))


def test_static_provider_answers_known_questions_only():
    provider = StaticProvider({"a": Answer(1)})
    assert provider("a") == Answer(Fraction(1))
    with pytest.raises(ProviderError, match="Keine Antwort für 'b'"):
        provider("b")


def test_collect_answers_keeps_case_order_and_marks_failures_as_unanswered():
    provider = StaticProvider({"b": Answer(2)})
    answers = collect_answers(CASES, provider)
    assert answers == (Answer(None), Answer(2))


def test_collect_answers_does_not_swallow_programming_errors():
    def broken(question):
        raise RuntimeError("Bug")

    with pytest.raises(RuntimeError, match="Bug"):
        collect_answers(CASES, broken)
    with pytest.raises(TypeError, match="Provider muss Answer liefern, nicht int"):
        collect_answers(CASES, lambda question: 1)


def test_collect_answers_for_no_cases_is_empty():
    assert collect_answers((), lambda question: Answer(0)) == ()
