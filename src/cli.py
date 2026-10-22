"""Kommandozeile: Freigabebericht erstellen und Berichte über die Zeit vergleichen.

::

    python -m aidataeco report SPEC [--answers DATEI] [--today JJJJ-MM-TT] [--expected-loss ZAHL]
                                    [--format markdown|json] [--output DATEI]
    python -m aidataeco compare ALT.json NEU.json [--format markdown|json] [--output DATEI]

Exit-Codes: ``0`` kein Freigabehindernis bzw. keine Regression, ``1`` Freigabehindernis bzw.
Regression, ``2`` ungültige Eingabe.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

from .compare import compare_reports
from .parsing import as_date, as_fraction
from .report import GoLiveReport, build_report
from .spec import answers_for, load_spec, read_document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aidataeco",
        description="Freigabebericht für ein Data Product erstellen und Berichte vergleichen.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("report", "compare"):
        sub = commands.add_parser(name)
        sub.add_argument("--format", choices=("markdown", "json"), default="markdown")
        sub.add_argument("--output", type=Path, help="Ausgabedatei statt Standardausgabe")
        if name == "report":
            sub.add_argument("spec", type=Path)
            sub.add_argument("--answers", type=Path, help="Antworten je Referenzfrage (.json/.yaml)")
            sub.add_argument("--today", help="Stichtag JJJJ-MM-TT (Standard: heutiges Datum)")
            sub.add_argument("--expected-loss", help="erwarteter Verlust E[L], exakt z. B. 3/2")
        else:
            sub.add_argument("old", type=Path)
            sub.add_argument("new", type=Path)
    return parser


def _emit(text: str, output: Optional[Path]) -> None:
    if output is None:
        sys.stdout.write(text)
    else:
        output.write_text(text, encoding="utf-8")


def _report(args: argparse.Namespace) -> int:
    spec = load_spec(args.spec)
    # Ohne Antwortdatei gilt jede Referenzfrage als unbeantwortet (kein Nachweis, kein Erfolg).
    answers = answers_for(spec, {} if args.answers is None else read_document(args.answers))
    today = date.today() if args.today is None else as_date("--today", args.today)
    loss = None if args.expected_loss is None else as_fraction("--expected-loss", args.expected_loss)
    report = build_report(spec, answers, today, loss)
    _emit(report.to_json() if args.format == "json" else report.to_markdown(), args.output)
    return 1 if report.blocked else 0


def _compare(args: argparse.Namespace) -> int:
    old = GoLiveReport.from_dict(read_document(args.old))
    new = GoLiveReport.from_dict(read_document(args.new))
    comparison = compare_reports(old, new)
    _emit(comparison.to_json() if args.format == "json" else comparison.to_markdown(), args.output)
    return 1 if comparison.has_regression else 0


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _report(args) if args.command == "report" else _compare(args)
    except (ValueError, OSError) as error:
        sys.stderr.write(f"Fehler: {error}\n")
        return 2
