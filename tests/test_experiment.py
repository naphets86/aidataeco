import json
from dataclasses import dataclass
from datetime import date
from enum import Enum
from fractions import Fraction

import pytest

from src import experiment
from src.experiment import ExperimentRecord, canonical_json, collect_versions, run_experiment


class Color(Enum):
    RED = 1


@dataclass
class Point:
    x: int


def test_canonical_json_is_deterministic_and_handles_model_types():
    text = canonical_json({"b": Fraction(1, 3), "a": date(2026, 10, 15), "s": {3, 1},
                           "e": Color.RED, "d": Point(2)})
    assert json.loads(text) == {"a": "2026-10-15", "b": "1/3", "d": {"x": 2}, "e": "RED", "s": [1, 3]}
    assert canonical_json({"x": 1, "y": 2}) == canonical_json({"y": 2, "x": 1})


def test_canonical_json_rejects_unknown_types():
    with pytest.raises(TypeError, match="Nicht serialisierbar: object"):
        canonical_json(object())
    with pytest.raises(TypeError, match="Nicht serialisierbar: type"):
        canonical_json(Point)


def test_collect_versions_marks_missing_packages_explicitly():
    versions = collect_versions(["definitely-not-installed-pkg", "pytest"])
    assert versions["definitely-not-installed-pkg"] is None
    assert versions["pytest"]
    assert versions["python"].count(".") >= 1
    assert "subgraph-sat-solver-econ" in collect_versions()
    assert experiment.DEPENDENCIES == ("subgraph-sat-solver-econ",)


def _record(**overrides) -> ExperimentRecord:
    values = dict(name="lauf1", config={"seed": 1}, inputs={"n": 3}, results={"ok": True},
                  versions={"python": "3"})
    values.update(overrides)
    return ExperimentRecord(**values)


def test_fingerprint_depends_on_inputs_config_and_versions_but_not_results():
    base = _record()
    assert base.fingerprint() == _record(results={"ok": False}).fingerprint()
    assert base.fingerprint() != _record(config={"seed": 2}).fingerprint()
    assert base.fingerprint() != _record(inputs={"n": 4}).fingerprint()
    assert base.fingerprint() != _record(versions={"python": "4"}).fingerprint()
    assert base.fingerprint() != _record(name="lauf2").fingerprint()


def test_record_round_trips_through_json_file(tmp_path):
    record = _record()
    path = record.write(tmp_path / "ergebnisse")
    assert path.name == "lauf1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fingerprint"] == record.fingerprint()
    assert data["results"] == {"ok": True}
    assert record.to_json().endswith("}\n")


@pytest.mark.parametrize("name", ["", "a/b", "..", "."])
def test_record_name_must_be_a_plain_file_name(name):
    with pytest.raises(ValueError, match="Dateiname"):
        _record(name=name)


def test_run_experiment_is_reproducible():
    def work(config, inputs):
        return {"sum": config["a"] + inputs["b"]}

    first = run_experiment("e", {"a": 1}, {"b": 2}, work, versions={"python": "x"})
    second = run_experiment("e", {"a": 1}, {"b": 2}, work, versions={"python": "x"})
    assert first.results == {"sum": 3}
    assert first.to_json() == second.to_json()
    collected = run_experiment("e", {"a": 1}, {"b": 2}, work)
    assert collected.versions == collect_versions()
