"""Freigabebericht (Go-live-Bericht) für ein Data Product (Abschnitt „Operationalisierung").

:func:`build_report` ist eine reine Funktion von Spezifikation, Antworten, Stichtag, erwartetem
Verlust und Versionen. Messbare Nachweise (Kennzahlen, Provenance, Qualität, Error Budget) werden
aus diesen Eingaben abgeleitet; fehlender Nachweis zählt nie als erfüllt. Der Bericht ist keine
Freigabe, sondern die Liste dessen, was einer Freigabe auf der angestrebten Stufe noch im Weg steht.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from typing import Dict, Mapping, Optional, Sequence, Tuple

from .errorbudget import is_good_enough
from .evaluation import Evaluation, evaluate, is_fresh
from .experiment import ExperimentRecord, canonical_json, collect_versions
from .governance import Evidence, ReliabilityLevel, release_blockers
from .model import Answer, DataProduct, Meaning, to_fraction
from .parsing import (as_bool, as_date, as_fraction, as_int, as_list, as_mapping, as_text,
                      check_keys, optional)
from .spec import Spec

EVIDENCE_LABELS: Mapping[str, str] = {
    "kpis_defined": "Kennzahlen definiert und verknüpft",
    "provenance_available": "Provenance vollständig",
    "quality_measurable": "Qualität messbar",
    "error_budget_met": "Error Budget eingehalten",
    "human_decides": "Ein Mensch entscheidet",
    "explicit_approval": "Ausdrückliche Freigabe",
    "logging": "Protokollierung",
    "intervention_path": "Eingriffspfad",
}


@dataclass(frozen=True)
class NodeStatus:
    """Zustand eines Knotens von ``V_P``; ``fresh`` ist ``None``, solange die Aktualisierung unbekannt ist."""

    name: str
    quality: Optional[Fraction]
    updated: Optional[date]
    fresh: Optional[bool]


@dataclass(frozen=True)
class GoLiveReport:
    """Ergebnis einer Prüfung; ``evaluation`` ist ``None`` ohne Referenzfragen."""

    product: str
    version: str
    owner: str
    level: ReliabilityLevel
    today: date
    missing_links: Tuple[Tuple[str, str], ...]
    nodes: Tuple[NodeStatus, ...]
    evaluation: Optional[Evaluation]
    min_pass_rate: Optional[Fraction]
    expected_loss: Optional[Fraction]
    budget_limit: Optional[Fraction]
    evidence: Evidence
    blockers: Tuple[str, ...]
    versions: Mapping[str, Optional[str]]
    fingerprint: str

    @property
    def blocked(self) -> bool:
        """``True``, wenn mindestens ein Freigabehindernis besteht."""
        return bool(self.blockers)

    def to_dict(self) -> Dict[str, object]:
        """JSON-fähige Darstellung; exakte Zahlen als Bruch-Text (``"3/4"``)."""
        evaluation = None if self.evaluation is None else {
            "pass_rate": str(self.evaluation.pass_rate),
            "provenance_coverage": str(self.evaluation.provenance_coverage),
            "unanswered": self.evaluation.unanswered,
        }
        return {
            "product": self.product,
            "version": self.version,
            "owner": self.owner,
            "level": self.level.name,
            "today": self.today.isoformat(),
            "missing_links": [list(link) for link in self.missing_links],
            "nodes": [{"name": node.name,
                       "quality": None if node.quality is None else str(node.quality),
                       "updated": None if node.updated is None else node.updated.isoformat(),
                       "fresh": node.fresh} for node in self.nodes],
            "evaluation": evaluation,
            "min_pass_rate": None if self.min_pass_rate is None else str(self.min_pass_rate),
            "expected_loss": None if self.expected_loss is None else str(self.expected_loss),
            "budget_limit": None if self.budget_limit is None else str(self.budget_limit),
            "evidence": dataclasses.asdict(self.evidence),
            "blocked": self.blocked,
            "blockers": list(self.blockers),
            "versions": dict(self.versions),
            "fingerprint": self.fingerprint,
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict()) + "\n"

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "GoLiveReport":
        """Liest einen gespeicherten Bericht streng wieder ein (Gegenstück zu :meth:`to_dict`)."""
        mapping = as_mapping("Bericht", data)
        keys = ("product", "version", "owner", "level", "today", "missing_links", "nodes",
                "evaluation", "min_pass_rate", "expected_loss", "budget_limit", "evidence",
                "blocked", "blockers", "versions", "fingerprint")
        check_keys("Bericht", mapping, keys)
        level = mapping["level"]
        if not isinstance(level, str) or level not in ReliabilityLevel.__members__:
            raise ValueError(f"Bericht: Unbekannte Stufe {level!r}")
        links = []
        for i, item in enumerate(as_list("Bericht.missing_links", mapping["missing_links"])):
            pair = [as_text(f"Bericht.missing_links[{i}]", part) for part in as_list(
                f"Bericht.missing_links[{i}]", item)]
            if len(pair) != 2:
                raise ValueError(f"Bericht.missing_links[{i}] muss zwei Knoten nennen")
            links.append((pair[0], pair[1]))
        nodes = []
        for i, item in enumerate(as_list("Bericht.nodes", mapping["nodes"])):
            name = f"Bericht.nodes[{i}]"
            node = as_mapping(name, item)
            check_keys(name, node, ("name", "quality", "updated", "fresh"))
            fresh = node["fresh"]
            nodes.append(NodeStatus(
                as_text(f"{name}.name", node["name"]),
                optional(as_fraction, f"{name}.quality", node["quality"]),
                optional(as_date, f"{name}.updated", node["updated"]),
                None if fresh is None else as_bool(f"{name}.fresh", fresh)))
        evaluation = None
        if mapping["evaluation"] is not None:
            ev = as_mapping("Bericht.evaluation", mapping["evaluation"])
            check_keys("Bericht.evaluation", ev, ("pass_rate", "provenance_coverage", "unanswered"))
            evaluation = Evaluation(as_fraction("Bericht.evaluation.pass_rate", ev["pass_rate"]),
                                    as_fraction("Bericht.evaluation.provenance_coverage",
                                                ev["provenance_coverage"]),
                                    as_int("Bericht.evaluation.unanswered", ev["unanswered"]))
        flags = as_mapping("Bericht.evidence", mapping["evidence"])
        names = [field.name for field in dataclasses.fields(Evidence)]
        check_keys("Bericht.evidence", flags, names)
        evidence = Evidence(**{n: as_bool(f"Bericht.evidence.{n}", flags[n]) for n in names})
        blockers = tuple(as_text(f"Bericht.blockers[{i}]", item)
                         for i, item in enumerate(as_list("Bericht.blockers", mapping["blockers"])))
        if as_bool("Bericht.blocked", mapping["blocked"]) != bool(blockers):
            raise ValueError("Bericht: blocked passt nicht zu blockers")
        versions = {as_text("Bericht.versions-Schlüssel", key): optional(as_text, "Bericht.versions", value)
                    for key, value in as_mapping("Bericht.versions", mapping["versions"]).items()}
        return cls(
            product=as_text("Bericht.product", mapping["product"]),
            version=as_text("Bericht.version", mapping["version"]),
            owner=as_text("Bericht.owner", mapping["owner"]),
            level=ReliabilityLevel[level],
            today=as_date("Bericht.today", mapping["today"]),
            missing_links=tuple(links),
            nodes=tuple(nodes),
            evaluation=evaluation,
            min_pass_rate=optional(as_fraction, "Bericht.min_pass_rate", mapping["min_pass_rate"]),
            expected_loss=optional(as_fraction, "Bericht.expected_loss", mapping["expected_loss"]),
            budget_limit=optional(as_fraction, "Bericht.budget_limit", mapping["budget_limit"]),
            evidence=evidence,
            blockers=blockers,
            versions=versions,
            fingerprint=as_text("Bericht.fingerprint", mapping["fingerprint"]),
        )

    def to_markdown(self) -> str:
        """Lesbare Fassung des Berichts (Zahlen exakt als Bruch, Prozentwerte gerundet)."""
        lines = [
            f"# Freigabebericht: {self.product}",
            "",
            f"- Version: {self.version}, Owner: {self.owner}",
            f"- Angestrebte Stufe: {int(self.level)} ({self.level.name})",
            f"- Stichtag: {self.today.isoformat()}",
            f"- Fingerprint: `{self.fingerprint}`",
            "",
            "## Ergebnis",
            "",
        ]
        if self.blocked:
            lines.append(f"**{len(self.blockers)} Freigabehindernis(se)** für Stufe {int(self.level)}.")
        else:
            lines.append(f"Für Stufe {int(self.level)} wurde kein Freigabehindernis festgestellt. "
                         "Das ist keine automatische Freigabe; die Entscheidung trifft der Use-Case Owner.")
        if self.blockers:
            lines += [""] + [f"- {blocker}" for blocker in self.blockers]
        lines += ["", "## Kennzahlen", "", "| Kennzahl | Wert |", "|---|---|"]
        if self.evaluation is None:
            lines.append("| Bestehensquote | nicht belegt (keine Referenzfragen) |")
            lines.append("| Provenance-Abdeckung | nicht belegt (keine Referenzfragen) |")
            lines.append("| Unbeantwortete Fragen | nicht belegt |")
        else:
            lines.append(f"| Bestehensquote | {_fraction_text(self.evaluation.pass_rate)} |")
            lines.append(f"| Provenance-Abdeckung | {_fraction_text(self.evaluation.provenance_coverage)} |")
            lines.append(f"| Unbeantwortete Fragen | {self.evaluation.unanswered} |")
        lines.append("| Mindest-Bestehensquote | "
                     + ("nicht festgelegt" if self.min_pass_rate is None else _fraction_text(self.min_pass_rate))
                     + " |")
        lines.append("| Erwarteter Verlust | "
                     + ("nicht belegt" if self.expected_loss is None else str(self.expected_loss)) + " |")
        lines.append("| Zulässiger Verlust ε·W | "
                     + ("nicht festgelegt" if self.budget_limit is None else str(self.budget_limit)) + " |")
        lines.append(f"| Offene Verknüpfungen | {len(self.missing_links)} |")
        lines += ["", "## Nachweise", "", "| Nachweis | Status |", "|---|---|"]
        for field in dataclasses.fields(Evidence):
            status = "belegt" if getattr(self.evidence, field.name) else "nicht belegt"
            lines.append(f"| {EVIDENCE_LABELS[field.name]} | {status} |")
        lines += ["", "## Knoten des Data Products", "", "| Knoten | Qualität | Aktualisiert | Aktuell |", "|---|---|---|---|"]
        for node in self.nodes:
            quality = "unbekannt" if node.quality is None else _fraction_text(node.quality)
            updated = "unbekannt" if node.updated is None else node.updated.isoformat()
            fresh = "unbekannt" if node.fresh is None else ("ja" if node.fresh else "nein")
            lines.append(f"| {_cell(node.name)} | {quality} | {updated} | {fresh} |")
        if self.missing_links:
            lines += ["", "## Offene Verknüpfungen", ""]
            lines += [f"- {_cell(start)} ↔ {_cell(goal)}" for start, goal in self.missing_links]
        lines += ["", "## Versionen", ""]
        lines += [f"- {name}: {version if version is not None else 'nicht installiert'}"
                  for name, version in sorted(self.versions.items())]
        return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _fraction_text(value: Fraction) -> str:
    percent = f"{float(value) * 100:.1f}".replace(".", ",")
    return f"{value} ({percent} %)"


def _defined(meaning: Meaning, term: str) -> bool:
    try:
        meaning.resolve(term)
    except ValueError:
        return False
    return True


def _node_status(product: DataProduct, name: str, today: date) -> NodeStatus:
    node = product.network.node(name)
    fresh = None if node.updated is None else is_fresh(node.updated, product.label.frequency_days, today)
    return NodeStatus(name, node.quality, node.updated, fresh)


def build_report(spec: Spec, answers: Sequence[Answer], today: date, expected_loss=None,
                 versions: Optional[Mapping[str, Optional[str]]] = None) -> GoLiveReport:
    """Prüft ``spec`` gegen ``answers`` zum Stichtag ``today``.

    ``answers`` stehen in der Reihenfolge der Referenzfälle. ``expected_loss`` ist der gemessene oder
    geschätzte erwartete Verlust ``E[L(ŷ, y*)]``; ohne ihn gilt das Error Budget als nicht belegt.
    """
    answers = tuple(answers)
    use_case = spec.use_case
    product = spec.product
    if not use_case.cases and answers:
        raise ValueError("Antworten ohne Referenzfälle in der Spezifikation")
    loss = None if expected_loss is None else to_fraction(expected_loss)
    if loss is not None and use_case.budget is None:
        raise ValueError("Erwarteter Verlust ohne Error Budget in der Spezifikation")
    evaluation = evaluate(use_case.cases, answers) if use_case.cases else None
    missing_links = product.missing_links(spec.required_links)
    nodes = tuple(_node_status(product, name, today) for name in sorted(product.node_names))
    declared = spec.declared
    evidence = Evidence(
        kpis_defined=bool(spec.kpis) and not missing_links
        and all(_defined(product.meaning, term) for term in spec.kpis),
        provenance_available=evaluation is not None and evaluation.provenance_coverage == 1,
        quality_measurable=bool(nodes) and all(node.quality is not None for node in nodes),
        error_budget_met=loss is not None and is_good_enough(loss, use_case.budget),
        human_decides=declared.human_decides,
        explicit_approval=declared.explicit_approval,
        logging=declared.logging,
        intervention_path=declared.intervention_path,
    )
    blockers = release_blockers(use_case.level, spec.accountabilities, evidence)
    if use_case.level >= ReliabilityLevel.DECISION_PREPARATION:
        blockers.extend(f"Aktualität nicht belegt: {node.name}" for node in nodes if node.fresh is not True)
    threshold = use_case.min_pass_rate
    if threshold is not None:
        if evaluation is None:
            blockers.append("Nachweis fehlt: Bestehensquote (keine Referenzfälle)")
        elif evaluation.pass_rate < threshold:
            # Ohne Zahlenwerte im Text: Das Hindernis ist ein Tag (B5 = {pass}); ändert sich nur die Quote,
            # ist es kein neues Hindernis, und der Vergleich meldet keine Regression.
            blockers.append("Bestehensquote liegt unter dem Mindestwert")
    versions = collect_versions() if versions is None else versions
    fingerprint = ExperimentRecord(
        name="golive", config=spec.raw,
        inputs={"answers": answers, "today": today, "expected_loss": loss},
        results={}, versions=versions).fingerprint()
    return GoLiveReport(
        product=product.name, version=product.label.version, owner=product.label.owner,
        level=use_case.level, today=today, missing_links=missing_links, nodes=nodes,
        evaluation=evaluation, min_pass_rate=threshold, expected_loss=loss,
        budget_limit=None if use_case.budget is None else use_case.budget.limit,
        evidence=evidence, blockers=tuple(blockers), versions=dict(versions), fingerprint=fingerprint,
    )
