"""HTTP-API für aidataeco.

Das Paket stellt die Bausteine aus ``src/`` (Importname ``aidataeco``) als zustandslose JSON-API bereit:
Freigabebericht und Regressionsvergleich, Auswertung von Referenzfragen, Error Budget, Diagnose von
Abweichungen, Vertrauensstufen, Auswahl von Datenquellen, Experimentprotokoll und die Fallstudie.

Module:

* :mod:`web.api` – FastAPI-Anwendung, Fehlerbehandlung und alle Endpunkte (Einstieg: ``web.api:app``)
* :mod:`web.schemas` – Request- und Response-Modelle mit Beschreibungen und Beispielen (OpenAPI)
* :mod:`web.convert` – Eingabeprüfung und Umwandlung zwischen JSON und den exakten Bausteinen aus ``src/``

``src/`` wird nicht verändert; die API ruft ausschließlich dessen öffentliche Funktionen auf.
"""
