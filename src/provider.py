"""Schnittstelle zur KI-Anwendung (Abschnitt „Operationalisierung als Prüfwerkzeug").

Ein :data:`AnswerProvider` beantwortet eine Referenzfrage mit einer :class:`~model.Answer`. Der Kern
kennt keine konkrete KI: Adapter (etwa für MCP) liefern nur diese Funktion. Kann ein Adapter keine
Antwort liefern, löst er :class:`ProviderError` aus; das zählt als „keine Antwort", nie als Erfolg.
Jede andere Ausnahme ist ein Programmfehler und wird nicht verschluckt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence, Tuple

from .evaluation import ReferenceCase
from .model import Answer

AnswerProvider = Callable[[str], Answer]


class ProviderError(Exception):
    """Der Adapter konnte keine Antwort liefern (nicht erreichbar, Zeitüberschreitung, …)."""


@dataclass(frozen=True)
class StaticProvider:
    """Feste Antworten je Frage, z. B. aus einer Datei; auch Testdouble für echte Adapter."""

    answers: Mapping[str, Answer]

    def __call__(self, question: str) -> Answer:
        try:
            return self.answers[question]
        except KeyError:
            raise ProviderError(f"Keine Antwort für {question!r} vorhanden") from None


def collect_answers(cases: Sequence[ReferenceCase], provider: AnswerProvider) -> Tuple[Answer, ...]:
    """Stellt jede Referenzfrage genau einmal; die Antworten stehen in der Reihenfolge der Fälle."""
    collected = []
    for case in cases:
        try:
            answer = provider(case.question)
        except ProviderError:
            answer = Answer(None)
        if not isinstance(answer, Answer):
            raise TypeError(f"Provider muss Answer liefern, nicht {type(answer).__name__}")
        collected.append(answer)
    return tuple(collected)
