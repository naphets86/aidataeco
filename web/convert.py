"""Eingabeprüfung und Umwandlung zwischen JSON und den exakten Bausteinen aus ``src/``.

Die Bibliothek rechnet ausschließlich mit :class:`fractions.Fraction` und löst bei ungültigen Eingaben
``ValueError`` aus. Dieses Modul schließt die Lücke zur JSON-Welt der API:

* Zahlen kommen als JSON-Zahl oder als Text (``"3/20"``, ``"0.15"``) und gehen als Bruch-Text
  (``"3/20"``) wieder hinaus – so wie in den JSON-Berichten der Kommandozeile.
* Zahlentexte mit riesigen Exponenten (``"1e999999999"``) würden beim Umwandeln in einen exakten Bruch
  Speicher und Rechenzeit verbrauchen. :func:`guard_numbers` und :func:`fraction` weisen sie ab.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, Mapping, Optional

from aidataeco.governance import Accountabilities, Evidence, ReliabilityLevel
from aidataeco.parsing import as_fraction

#: Größter zulässiger Exponent (Anzahl Ziffern) in Zahlentexten wie ``"1e100"``.
MAX_EXPONENT_DIGITS = 3

# Ein Zahlentext mit Exponenten; Texte, die nur zufällig ein „e“ enthalten (z. B. Hex-Fingerprints), passen nicht.
_EXPONENT_NUMBER = re.compile(r"\s*[+-]?(?=[\d.])[\d_.]*[eE][+-]?(?P<exp>[\d_]+)\s*")

#: Rolle der KI je Stufe (Tabelle „Nutzungsstufen nach erforderlicher Zuverlässigkeit" der Arbeit).
LEVEL_ROLES: Mapping[ReliabilityLevel, str] = {
    ReliabilityLevel.HINT: "Hinweis",
    ReliabilityLevel.CROSS_CHECK: "Gegenprüfung",
    ReliabilityLevel.DECISION_PREPARATION: "Vorbereitung von Entscheidungen",
    ReliabilityLevel.AUTOMATED_ACTION: "Automatisierte Handlung",
}


def text(value: Fraction) -> str:
    """Exakte Zahl als Text, ganze Zahlen ohne Nenner (``"3"``, ``"3/20"``)."""
    return str(value)


def optional_text(value: Optional[Fraction]) -> Optional[str]:
    """Wie :func:`text`; ``None`` (kein Nachweis) bleibt ``None``."""
    return None if value is None else text(value)


def _reject_huge_exponent(name: str, value: str) -> None:
    match = _EXPONENT_NUMBER.fullmatch(value)
    if match is not None and len(match["exp"].replace("_", "")) > MAX_EXPONENT_DIGITS:
        raise ValueError(
            f"{name}: Exponenten mit mehr als {MAX_EXPONENT_DIGITS} Ziffern sind nicht zulässig")


def fraction(name: str, value: object) -> Fraction:
    """Exakte Zahl aus JSON; ungültige oder übergroße Angaben lösen ``ValueError`` aus."""
    if isinstance(value, str):
        _reject_huge_exponent(name, value)
    return as_fraction(name, value)


def optional_fraction(name: str, value: object) -> Optional[Fraction]:
    """Wie :func:`fraction`; ``None`` bleibt ``None``."""
    return None if value is None else fraction(name, value)


def fractions_of(name: str, values: Mapping[str, object]) -> Dict[str, Fraction]:
    """Wandelt alle Werte eines Mappings in exakte Zahlen um."""
    return {key: fraction(f"{name}[{key!r}]", value) for key, value in values.items()}


def guard_numbers(data: object, name: str = "Eingabe") -> None:
    """Prüft alle Texte in einer beliebig verschachtelten JSON-Struktur auf übergroße Exponenten.

    Gedacht für frei strukturierte Dokumente (Spezifikation, Antworten, Berichte), die erst in der
    Bibliothek zu Zahlen werden. Die Prüfung ist iterativ und damit unabhängig von der Verschachtelungstiefe.
    """
    stack = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            _reject_huge_exponent(name, item)
        elif isinstance(item, Mapping):
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)


def level_of(value: object) -> ReliabilityLevel:
    """Stufe aus ihrer Nummer (``1`` bis ``4``) oder ihrem Namen (``"HINT"`` …)."""
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return ReliabilityLevel(value)
        except ValueError:
            raise ValueError(f"Stufe muss 1 bis 4 sein, nicht {value}") from None
    if isinstance(value, str) and value in ReliabilityLevel.__members__:
        return ReliabilityLevel[value]
    raise ValueError(f"Unbekannte Stufe {value!r}")


def accountabilities_of(roles: Mapping[str, Optional[str]]) -> Accountabilities:
    """Verantwortliche Personen aus einem Mapping; fehlende Rollen bleiben unbenannt (``None``)."""
    return Accountabilities(**roles)


def evidence_of(flags: Mapping[str, bool]) -> Evidence:
    """Nachweise aus einem Mapping von Feldname auf ``bool``."""
    return Evidence(**flags)
