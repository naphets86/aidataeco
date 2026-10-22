"""aidataeco: ausführbare Bausteine zur Arbeit „Wann ist das Datennetz gut genug für KI?".

Module (Abschnitte der Arbeit in Klammern):

* :mod:`model` – Datennetz, Data Product, Label, Provenance (Formales Modell)
* :mod:`errorbudget` – Stakes, Error Budget, Fehlerzerlegung, Gut-genug-Bedingung
* :mod:`diagnosis` – Abweichungen als Bayes-Indikator, Lern-Loop, VOI-Bedingung
* :mod:`governance` – Vertrauensstufen, Verantwortlichkeiten, Freigabe
* :mod:`evaluation` – Testfragen, Bestehensquote, erklärter Anteil, Provenance-Abdeckung
* :mod:`integration` – Auswahl von Datenquellen mit dem Solver aus ``subgraph-sat-solver-econ``
* :mod:`experiment` – reproduzierbares Protokoll von Eingaben, Konfiguration, Versionen, Resultaten
* :mod:`casestudy` – illustrative Fallstudie „Warum sinkt die Marge?"

Entscheider, Schaltkreise und Wohlfahrtsformeln werden **nicht** neu implementiert, sondern aus dem
Paket ``subgraph_sat_solver_econ`` (Abhängigkeit in ``pyproject.toml``) wiederverwendet.
"""
