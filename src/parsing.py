"""Strenges Einlesen von Spezifikationen, Antworten und Berichten aus Mappings (JSON/YAML).

Leitplanke wie im Modell: Unbekannte Felder, falsche Typen und ungültige Zahlen lösen
``ValueError`` aus. Nichts wird stillschweigend ignoriert oder durch einen Standardwert ersetzt.
"""

from __future__ import annotations

from datetime import date, datetime
from fractions import Fraction
from typing import Callable, Iterable, List, Mapping, Optional, TypeVar

from .model import to_fraction

T = TypeVar("T")


def as_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} muss ein Mapping sein")
    return value


def as_list(name: str, value: object) -> List[object]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} muss eine Liste sein")
    return list(value)


def check_keys(name: str, mapping: Mapping[str, object], required: Iterable[str] = (),
               optional: Iterable[str] = ()) -> None:
    """Pflichtfelder müssen vorhanden sein; Felder außerhalb von Pflicht und Optional sind verboten."""
    required, optional = tuple(required), tuple(optional)
    missing = sorted(set(required) - set(mapping))
    if missing:
        raise ValueError(f"{name}: Pflichtfeld fehlt: {', '.join(missing)}")
    unknown = sorted(str(key) for key in set(mapping) - set(required) - set(optional))
    if unknown:
        raise ValueError(f"{name}: Unbekannte Felder: {', '.join(unknown)}")


def as_text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} muss ein Text sein (in YAML ggf. in Anführungszeichen setzen)")
    return value


def as_bool(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} muss true oder false sein")
    return value


def as_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} muss eine ganze Zahl sein")
    return value


def as_fraction(name: str, value: object) -> Fraction:
    """Exakte Zahl aus ``int``, ``float``, ``Fraction`` oder Text (``"3/20"``, ``"0.15"``)."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Fraction)):
        raise ValueError(f"{name} muss eine Zahl sein")
    try:
        return to_fraction(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"{name}: {value!r} ist keine gültige Zahl") from None


def as_date(name: str, value: object) -> date:
    """Datum als ``date`` oder ISO-Text ``JJJJ-MM-TT``; Zeitstempel mit Uhrzeit werden abgelehnt."""
    if isinstance(value, datetime):
        raise ValueError(f"{name} muss ein Datum ohne Uhrzeit sein")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{name}: {value!r} ist kein Datum (JJJJ-MM-TT)") from None
    raise ValueError(f"{name} muss ein Datum sein")


def optional(parser: Callable[[str, object], T], name: str, value: object) -> Optional[T]:
    """``None`` bleibt ``None`` (unbekannt); sonst wird mit ``parser`` gelesen."""
    return None if value is None else parser(name, value)
