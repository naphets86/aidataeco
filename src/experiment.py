"""Reproduzierbarer Experimentpfad: Eingaben, Konfiguration, Versionen und Resultate protokollieren.

Das Protokoll enthält bewusst keine Zeitstempel; so ist derselbe Lauf bitgleich wiederholbar. Ein
nicht installiertes Paket wird als ``None`` ausgewiesen, nicht weggelassen.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import date
from enum import Enum
from fractions import Fraction
from importlib import metadata
from pathlib import Path
from typing import Callable, Dict, Iterable, Mapping, Optional

DEPENDENCIES = ("subgraph-sat-solver-econ",)


def _encode(value: object) -> object:
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    if isinstance(value, Enum):
        return value.name
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    raise TypeError(f"Nicht serialisierbar: {type(value).__name__}")


def canonical_json(value: object) -> str:
    """Deterministische JSON-Darstellung (sortierte Schlüssel, ``Fraction`` als ``"p/q"``)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, default=_encode)


def collect_versions(packages: Iterable[str] = DEPENDENCIES) -> Dict[str, Optional[str]]:
    """Versionen von Python und Abhängigkeiten; ``None`` für nicht installierte Pakete."""
    versions: Dict[str, Optional[str]] = {"python": sys.version.split()[0]}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    return versions


@dataclass(frozen=True)
class ExperimentRecord:
    """Protokoll eines Experiments; ``fingerprint`` bindet Eingaben, Konfiguration und Versionen."""

    name: str
    config: Mapping[str, object]
    inputs: Mapping[str, object]
    results: Mapping[str, object]
    versions: Mapping[str, Optional[str]]

    def __post_init__(self) -> None:
        if not self.name or Path(self.name).name != self.name or self.name in (".", ".."):
            raise ValueError("Experimentname muss ein einfacher Dateiname sein")

    def fingerprint(self) -> str:
        payload = {"name": self.name, "config": self.config, "inputs": self.inputs,
                   "versions": self.versions}
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def to_json(self) -> str:
        return canonical_json({
            "name": self.name,
            "fingerprint": self.fingerprint(),
            "config": self.config,
            "inputs": self.inputs,
            "versions": self.versions,
            "results": self.results,
        }) + "\n"

    def write(self, directory: Path) -> Path:
        """Schreibt ``<name>.json`` in ``directory`` (wird bei Bedarf angelegt)."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.name}.json"
        path.write_text(self.to_json(), encoding="utf-8")
        return path


def run_experiment(name: str, config: Mapping[str, object], inputs: Mapping[str, object],
                   function: Callable[[Mapping[str, object], Mapping[str, object]], Mapping[str, object]],
                   versions: Optional[Mapping[str, Optional[str]]] = None) -> ExperimentRecord:
    """Führt ``function(config, inputs)`` aus und protokolliert das Ergebnis."""
    results = function(config, inputs)
    return ExperimentRecord(name, config, inputs, results,
                            collect_versions() if versions is None else versions)
