import json
import runpy
import sys

import pytest

from src.cli import main

from sample_data import Q1, as_json, base_answers, base_data


def _files(tmp_path, data=None, answers=None):
    spec = tmp_path / "spec.json"
    spec.write_text(as_json(base_data() if data is None else data), encoding="utf-8")
    given = tmp_path / "answers.json"
    given.write_text(as_json(base_answers() if answers is None else answers), encoding="utf-8")
    return str(spec), str(given)


def test_report_prints_markdown_and_signals_a_clean_release_with_exit_code_zero(tmp_path, capsys):
    spec, answers = _files(tmp_path)
    code = main(["report", spec, "--answers", answers, "--today", "2026-10-22", "--expected-loss", "5"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("# Freigabebericht: Sales Result 360") and "kein Freigabehindernis" in out


def test_report_writes_json_and_blocks_with_exit_code_one(tmp_path, capsys):
    spec, answers = _files(tmp_path)
    target = tmp_path / "bericht.json"
    code = main(["report", spec, "--answers", answers, "--today", "2026-10-22", "--format", "json",
                 "--output", str(target)])
    assert code == 1 and capsys.readouterr().out == ""
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["blocked"] is True and data["expected_loss"] is None
    assert data["evaluation"]["pass_rate"] == "1"


def test_report_without_answers_leaves_the_questions_unevidenced(tmp_path, capsys):
    spec, _ = _files(tmp_path)
    assert main(["report", "--format", "json", spec, "--today", "2026-10-22"]) == 1
    evaluation = json.loads(capsys.readouterr().out)["evaluation"]
    assert evaluation == {"pass_rate": "0", "provenance_coverage": "0", "unanswered": 2}
    data = base_data()
    del data["use_case"]["reference_cases"]
    spec, _ = _files(tmp_path, data)
    assert main(["report", spec, "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["evaluation"] is None


@pytest.mark.parametrize("extra,message", [
    (["--today", "gestern"], "kein Datum"),
    (["--expected-loss", "viel"], "keine gültige Zahl"),
    (["--answers", "fehlt.json"], "fehlt.json"),
])
def test_invalid_input_exits_with_code_two(tmp_path, capsys, extra, message):
    spec, _ = _files(tmp_path)
    assert main(["report", spec, *extra]) == 2
    assert message in capsys.readouterr().err


def test_unknown_questions_in_answers_are_an_error(tmp_path, capsys):
    answers = base_answers()
    answers["Tippfehler"] = {"value": 1}
    spec, given = _files(tmp_path, answers=answers)
    assert main(["report", spec, "--answers", given]) == 2
    assert "unbekannten Fragen" in capsys.readouterr().err


def test_compare_detects_regressions_between_stored_reports(tmp_path, capsys):
    spec, answers = _files(tmp_path)
    good, bad = tmp_path / "gut.json", tmp_path / "schlecht.json"
    main(["report", spec, "--answers", answers, "--today", "2026-10-22", "--expected-loss", "5",
          "--format", "json", "--output", str(good)])
    main(["report", spec, "--answers", answers, "--today", "2026-10-22", "--format", "json",
          "--output", str(bad)])
    capsys.readouterr()
    assert main(["compare", str(good), str(good)]) == 0
    assert "Keine Regression." in capsys.readouterr().out
    assert main(["compare", str(good), str(bad), "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["has_regression"] is True
    assert main(["compare", str(bad), str(good)]) == 0
    capsys.readouterr()
    broken = tmp_path / "kaputt.json"
    broken.write_text('{"product": "x"}', encoding="utf-8")
    assert main(["compare", str(good), str(broken)]) == 2
    assert "Pflichtfeld fehlt" in capsys.readouterr().err


def test_module_entry_point_exits_with_the_command_status(tmp_path, monkeypatch):
    spec, answers = _files(tmp_path)
    monkeypatch.setattr(sys, "argv", ["aidataeco", "report", spec, "--answers", answers,
                                      "--today", "2026-10-22", "--expected-loss", "5",
                                      "--output", str(tmp_path / "out.md")])
    with pytest.raises(SystemExit) as stop:
        runpy.run_module("src", run_name="__main__")
    assert stop.value.code == 0
    assert (tmp_path / "out.md").read_text(encoding="utf-8").startswith("# Freigabebericht")
