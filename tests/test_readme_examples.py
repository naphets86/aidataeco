"""Führt die Python-Beispiele der README aus und vergleicht ihre Ausgaben mit dem gezeigten Text.

Die README zeigt im Abschnitt „Prüfwerkzeug und Python-API" (zwischen den Markierungen
``api-beispiele:start`` und ``api-beispiele:end``) Python-Beispiele, die aufeinander aufbauen und
eine gemeinsame Sitzung nutzen. Folgt einem Beispiel unmittelbar ein ``text``-Block, ist das seine
Ausgabe. Beispiele mit dem Zusatz ``python skip`` werden nur auf gültige Syntax geprüft (sie brauchen
Netzwerk oder fremde Daten).
"""

import contextlib
import importlib
import io
import re
import shutil
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- api-beispiele:start -->"
END = "<!-- api-beispiele:end -->"
FENCE = re.compile(r"```(\w*)(?: (\w+))?\n(.*?)```", re.S)


def _install_package_alias():
    """Die README importiert ``aidataeco``; im Entwicklungsbaum ohne Installation liegt das Paket in ``src/``."""
    try:
        importlib.import_module("aidataeco")
    except ImportError:
        alias = types.ModuleType("aidataeco")
        alias.__path__ = [str(ROOT / "src")]
        sys.modules["aidataeco"] = alias


def _fences():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    region = text.split(START, 1)[1].split(END, 1)[0]
    return region, list(FENCE.finditer(region))


def _examples(skipped):
    """Python-Beispiele mit ihrer dokumentierten Ausgabe (``None``, wenn keine gezeigt wird)."""
    region, fences = _fences()
    examples = []
    for index, fence in enumerate(fences):
        language, flag, code = fence.groups()
        if language != "python" or (flag == "skip") != skipped:
            continue
        expected = None
        if index + 1 < len(fences):
            following = fences[index + 1]
            if following.group(1) == "text" and not region[fence.end():following.start()].strip():
                expected = following.group(3)
        examples.append((code, expected))
    return examples


def test_readme_examples_run_and_print_the_documented_output(tmp_path, monkeypatch):
    pytest.importorskip("yaml")
    _install_package_alias()
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    monkeypatch.chdir(tmp_path)
    examples = _examples(skipped=False)
    assert len(examples) >= 15
    namespace = {"__name__": "readme"}
    for number, (code, expected) in enumerate(examples, 1):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile(code, f"README-Beispiel {number}", "exec"), namespace)
        printed = buffer.getvalue().strip()
        if expected is None:
            assert printed == "", f"Beispiel {number} gibt aus, zeigt aber keine Ausgabe:\n{printed}"
        else:
            assert printed == expected.strip(), f"Beispiel {number}: Ausgabe weicht von der README ab"


def test_skipped_readme_examples_are_valid_python():
    skipped = _examples(skipped=True)
    assert len(skipped) >= 2
    for number, (code, expected) in enumerate(skipped, 1):
        assert expected is None
        compile(code, f"README-Beispiel (skip) {number}", "exec")


def test_readme_documents_every_cli_option_and_exit_code():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for option in ("--answers", "--today", "--expected-loss", "--format", "--output"):
        assert f"`{option}" in text
    for command in ("`report SPEC`", "`compare ALT NEU`"):
        assert command in text
