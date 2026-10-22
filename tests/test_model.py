from datetime import date
from fractions import Fraction

import pytest

from src.model import (
    Answer,
    DataNetwork,
    DataProduct,
    Edge,
    Label,
    Meaning,
    Node,
    Provenance,
    to_fraction,
    unit_fraction,
)


def _network() -> DataNetwork:
    return DataNetwork(
        nodes=(
            Node("auftrag", {"umsatz", "rabatt"}, 0.9, date(2026, 9, 30)),
            Node("lieferung"),
            Node("fracht", {"kosten"}),
        ),
        edges=(
            Edge("auftrag", "lieferung", "auftrag_id"),
            Edge("fracht", "lieferung", "lieferung_id"),
            Edge("fracht", "lieferung", "lieferung_id_alt"),
        ),
    )


def _label() -> Label:
    return Label(owner="Controlling", version="1.0", frequency_days=1)


def test_number_helpers_are_exact_and_validate_range():
    assert to_fraction(0.1) == Fraction(1, 10)
    assert to_fraction(3) == Fraction(3)
    assert unit_fraction("q", Fraction(1, 2)) == Fraction(1, 2)
    with pytest.raises(ValueError, match="q muss in \\[0, 1\\] liegen"):
        unit_fraction("q", 2)


def test_node_normalizes_fields_and_keeps_unknowns_explicit():
    node = Node("  tabelle ", ["a", "a", "b"], 0.9)
    assert node.name == "tabelle"
    assert node.attributes == frozenset({"a", "b"})
    assert node.quality == Fraction(9, 10)
    unknown = Node("x")
    assert unknown.quality is None and unknown.updated is None
    with pytest.raises(ValueError, match="Knotenname"):
        Node("   ")
    with pytest.raises(ValueError, match="Knotenname"):
        Node(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Qualität"):
        Node("x", quality=1.5)


def test_network_is_a_multigraph_with_checked_references():
    network = _network()
    assert len(network.edges) == 3
    assert network.node("fracht").attributes == frozenset({"kosten"})
    with pytest.raises(ValueError, match="Unbekannter Knoten"):
        network.node("fehlt")
    with pytest.raises(ValueError, match="eindeutig"):
        DataNetwork((Node("a"), Node("a")))
    with pytest.raises(ValueError, match="unbekannten Knoten 'b'"):
        DataNetwork((Node("a"),), (Edge("a", "b", "t"),))
    with pytest.raises(ValueError, match="unbekannten Knoten 'z'"):
        DataNetwork((Node("a"),), (Edge("z", "a", "t"),))


def test_meaning_resolves_terms_and_synonyms_without_defaults():
    meaning = Meaning({"marge": "DB II / Umsatz"}, {"Rohertrag": "marge"}, ["Marge ist DB II"])
    assert meaning.resolve("marge") == "DB II / Umsatz"
    assert meaning.resolve("Rohertrag") == "DB II / Umsatz"
    assert meaning.rules == ("Marge ist DB II",)
    assert Meaning({}).synonyms == {}
    with pytest.raises(ValueError, match="nicht definiert"):
        meaning.resolve("umsatz")


def test_label_requires_explicit_owner_and_version():
    label = Label(" Controlling ", " 2 ", 7, 0.99)
    assert (label.owner, label.version, label.quality) == ("Controlling", "2", Fraction(99, 100))
    with pytest.raises(ValueError, match="Owner"):
        Label("", "1", 1)
    with pytest.raises(ValueError, match="Version"):
        Label("a", " ", 1)
    with pytest.raises(ValueError, match="positiv"):
        Label("a", "1", 0)
    with pytest.raises(ValueError, match="Qualität"):
        Label("a", "1", 1, quality=-0.1)


def test_data_product_must_be_a_subnetwork():
    network = _network()
    product = DataProduct(
        "Sales Result 360", network, ["auftrag", "lieferung"], [network.edges[0]], Meaning({}), _label()
    )
    assert product.name == "Sales Result 360"
    assert product.node_names == frozenset({"auftrag", "lieferung"})
    with pytest.raises(ValueError, match="Name"):
        DataProduct(" ", network, [], [], Meaning({}), _label())
    with pytest.raises(ValueError, match="V_P"):
        DataProduct("p", network, ["unbekannt"], [], Meaning({}), _label())
    with pytest.raises(ValueError, match="E_P"):
        DataProduct("p", network, ["auftrag"], [Edge("auftrag", "lieferung", "x")], Meaning({}), _label())
    with pytest.raises(ValueError, match="nur Knoten von P"):
        DataProduct("p", network, ["auftrag"], [network.edges[0]], Meaning({}), _label())
    with pytest.raises(ValueError, match="nur Knoten von P"):
        DataProduct("p", network, ["lieferung"], [network.edges[0]], Meaning({}), _label())


def test_missing_links_finds_unconnected_freight():
    network = _network()
    open_product = DataProduct(
        "p", network, ["auftrag", "lieferung", "fracht"], [network.edges[0]], Meaning({}), _label()
    )
    required = [("auftrag", "fracht")]
    assert open_product.missing_links(required) == (("auftrag", "fracht"),)
    assert not open_product.is_closed(required)

    closed = DataProduct(
        "p", network, ["auftrag", "lieferung", "fracht"], list(network.edges), Meaning({}), _label()
    )
    assert closed.missing_links(required) == ()
    assert closed.is_closed(required)
    assert closed.is_closed([("fracht", "auftrag"), ("auftrag", "auftrag")])


def test_missing_links_reports_nodes_outside_the_product():
    network = _network()
    product = DataProduct("p", network, ["auftrag"], [], Meaning({}), _label())
    assert product.missing_links([("auftrag", "fracht"), ("fracht", "auftrag")]) == (
        ("auftrag", "fracht"),
        ("fracht", "auftrag"),
    )


def test_provenance_lists_what_is_missing():
    empty = Provenance()
    assert empty.missing() == ("Quelle", "Datenstichtag", "Definition")
    assert not empty.is_complete()
    full = Provenance((("Sales Result 360", "1.0"),), date(2026, 9, 30), ("Marge ist DB II",))
    assert full.missing() == ()
    assert full.is_complete()
    assert Provenance(cutoff=date(2026, 9, 30)).missing() == ("Quelle", "Definition")


def test_answer_converts_values_and_allows_no_answer():
    assert Answer(0.25).value == Fraction(1, 4)
    assert Answer(None).value is None
    assert Answer(1).provenance is None
