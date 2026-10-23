"""Gemeinsame Testkonfiguration.

Die Web-API importiert die Bausteine unter ihrem Paketnamen ``aidataeco`` (so wie ein installiertes Paket).
Im Entwicklungsbaum ohne Installation liegt das Paket in ``src/``; dann wird ``aidataeco`` als Alias auf
dieses Verzeichnis eingerichtet, so wie es auch ``test_readme_examples.py`` tut. ``src/`` selbst bleibt unverändert.
"""

import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    importlib.import_module("aidataeco")
except ImportError:  # pragma: no cover - hängt davon ab, ob das Paket installiert ist
    alias = types.ModuleType("aidataeco")
    alias.__path__ = [str(ROOT / "src")]
    sys.modules["aidataeco"] = alias
