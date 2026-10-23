# Wann ist das Datennetz gut genug für KI?

**Ein ökonomischer und formaler Ansatz zur verantwortbaren Nutzung von KI in Unternehmen**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-291%20passed-4c1)](tests/)
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-100%25-brightgreen)](doc/coverage/index.html)
[![scicov](https://img.shields.io/badge/scicov-10-ff69b4)](doc/coverage/index.html)

Dieses Repository enthält eine wissenschaftliche Arbeit über die Frage, wann das Datennetz eines Unternehmens für eine bestimmte KI-Anwendung gut genug ist. Im Mittelpunkt steht nicht die Suche nach fehlerfreien Daten oder einem perfekten Modell. Entscheidend ist, ob die verbleibende Unsicherheit für den jeweiligen Zweck und die möglichen Folgen einer Entscheidung vertretbar ist.

Die Arbeit verbindet ein formales Modell von Datennetzen und Data Products mit einer wirtschaftlichen Betrachtung von Fehlerbudgets, einer Fallstudie zur Margenanalyse und einem schrittweisen Vorgehen für Organisationen. KI wird dabei zunächst als Hinweis- und Gegenprüfungswerkzeug verstanden. Abweichungen zwischen KI-Antwort und Unternehmensanalyse können auf Datenlücken hinweisen, aber auch eine unvollständige interne Analyse sichtbar machen.

> **Leitgedanke:** Nicht nur fragen, ob die KI gut genug ist, sondern ob das Datennetz für diese konkrete Frage gut genug ist.

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Kernaussagen](#kernaussagen)
- [Inhalt der Arbeit](#inhalt-der-arbeit)
- [Fallstudie: Sinkende Marge](#fallstudie-sinkende-marge)
- [Formales Modell und wirtschaftliche Perspektive](#formales-modell-und-wirtschaftliche-perspektive)
- [Vertrauensstufen](#vertrauensstufen)
- [Data Products und Verantwortlichkeiten](#data-products-und-verantwortlichkeiten)
- [Voraussetzungen](#voraussetzungen)
- [PDF erstellen](#pdf-erstellen)
- [Prüfen und weiterentwickeln](#prüfen-und-weiterentwickeln)
- [Stand und Grenzen](#stand-und-grenzen)
- [Quellen und weiterführende Arbeiten](#quellen-und-weiterführende-arbeiten)
- [Software und Tests](#software-und-tests)
- [Prüfwerkzeug und Python-API (Operationalisierung)](#prüfwerkzeug-und-python-api-operationalisierung)
- [JSON-API (FastAPI)](#json-api-fastapi)
- [Erwerb](#erwerb)

## Überblick

Die Verlässlichkeit einer KI-Antwort entsteht nicht allein durch das KI-Modell. Sie hängt auch davon ab, ob relevante Daten zugänglich, aktuell, fachlich verständlich und miteinander verbunden sind. Wenn zum Beispiel Frachtkosten in einem Logistiksystem liegen, aber keiner Bestellung zugeordnet werden können, kann eine KI eine Margenveränderung nicht vollständig erklären – unabhängig davon, wie gut sie formuliert.

Die Arbeit behandelt die Datenlandschaft als ein **Datennetz**: Datenbestände und Dokumente bilden Knoten; fachliche Beziehungen, Joins und Transformationen bilden Kanten. Ein **Data Product** stellt einen für einen Geschäftsbereich relevanten und wiederverwendbaren Teil dieses Netzes bereit. Es bündelt:

1. **Daten** und ihre Granularität,
2. **Bedeutung** wie Definitionen, Synonyme und fachliche Regeln,
3. **Label** mit Eigentümerschaft, Qualität, Aktualität, Zugriff und Version.

Auf dieser Grundlage wird eine KI-Antwort nach dem Verwendungszweck bewertet. Ein Hinweis für eine fachliche Prüfung darf größere Unsicherheit haben als eine Handlung, die ohne menschliche Kontrolle ausgelöst wird. Die notwendige Qualität ist daher an die **Stakes** – die möglichen wirtschaftlichen und organisatorischen Folgen – und an ein anwendungsbezogenes **Error Budget** gebunden.

## Kernaussagen

- **Fehlerfreiheit ist keine realistische Voraussetzung.** Entscheidend ist, ob der mögliche Fehler für den konkreten Einsatz klein genug ist.
- **Die Frage bestimmt den erforderlichen Reifegrad.** Dasselbe Datennetz kann für eine Trendbeobachtung genügen und für eine Kunden- oder Preisentscheidung unzureichend sein.
- **Das Datennetz ist mehr als eine Sammlung von Tabellen.** Beziehungen zwischen Quellen, Definitionen, Zugriff und Aktualität sind ebenso wichtig wie die Daten selbst.
- **Ein plausibler Text ist kein Korrektheitsnachweis.** Antworten sollten Definition, Quelle und Datenstichtag erkennen lassen und gegen eine belastbare Referenz geprüft werden.
- **KI kann schon vor vollständiger Datenreife nützlich sein.** Als Hinweis oder Gegenprüfung unterstützt sie die Analyse, ohne selbst als alleinige Entscheidungsinstanz zu gelten.
- **Abweichungen sind Diagnoseanlässe.** Ursachen können fehlende Daten, fehlende Attribute, Definitionskonflikte, veraltete Daten oder Fehler in der eigenen Analyse sein.
- **Data Products ermöglichen Wiederverwendung.** Gemeinsame Daten und Definitionen können mehrere Anwendungen versorgen, statt in jedem Projekt neu aufgebaut zu werden.
- **Verantwortung braucht benannte Personen.** Bedeutung, Lieferung und Freigabe der jeweiligen Anwendung sind getrennte Verantwortungsbereiche.
- **Autonomie wird stufenweise aufgebaut.** Automatisierte Handlungen erfordern strengere Qualitätsnachweise, Freigaben und Protokollierung als unverbindliche Hinweise.

## Inhalt der Arbeit

Die LaTeX-Arbeit entwickelt das Konzept in folgender Reihenfolge:

1. **Ausgangslage: KI-Ambition und Datenreife** – ordnet den im Webinar beschriebenen Abstand zwischen KI-Einsatz und Datenreife ein.
2. **Fallstudie: Warum sinkt die Marge?** – zeigt an einem konkreten Beispiel, wie eine teilweise richtige Erklärung eine falsche Maßnahme nahelegen kann.
3. **Formales Modell des Datennetzes** – beschreibt Datenbestände, Beziehungen, Einflussgrößen, Data Products und Provenance.
4. **Fehlerzusammensetzung und „gut genug“** – führt Error Budget, Stakes und anwendungsbezogene Anforderungen ein.
5. **Abweichungen als Chance** – betrachtet Unterschiede zwischen KI-Antwort und interner Analyse als diagnostisches Signal und entwickelt einen Lernkreislauf.
6. **Das Data Product als gemeinsame Grundlage** – konkretisiert Daten, Granularität, Meaning und Label anhand eines Beispiels.
7. **Verantwortung und Freigabe** – erläutert Data Owner, Data Product Owner und Use-Case Owner.
8. **Schrittweises Vorgehen in der Praxis** – beschreibt den Aufbau und unterscheidet Schwerpunkte für Mittelstand und Großunternehmen.
9. **Stolperfallen, Fortschrittsmessung und Checkliste** – gibt Prüffragen und Kennzahlen für die praktische Anwendung.
10. **Operationalisierung: Freigabebericht und Regression** – macht die Kriterien zu einem deterministischen Prüfverfahren mit maschinenlesbarer Spezifikation, abgeleiteten Nachweisen, Freigabehindernissen und Vergleich über die Zeit; die Eigenschaften werden bewiesen (steht im PDF vor der Checkliste).
11. **Diskussion, Schlussfolgerung und Glossar** – fasst die Grenzen des Modells und die zentralen Aussagen zusammen.
12. **Anhang** – enthält formale Erweiterungen und eine Beweisskizze zur Value of Information (VOI).

Das vollständige Inhaltsverzeichnis steht auch am Anfang des [PDFs](science/aidataeco.pdf).

## Fallstudie: Sinkende Marge

Die illustrative Webinar-Fallstudie betrachtet einen Maschinenbauzulieferer. Der Umsatz steigt von 10,0 Mio. € auf 11,0 Mio. €, während die Deckungsbeitragsmarge II von 28 % auf 24 % fällt. Die daraus abgeleitete DB-II-Differenz beträgt 440 T€.

| Ursache | Betrag | Anteil an der Differenz | Sichtbar für die KI? |
|---|---:|---:|---|
| Expressfracht nach Lieferengpass | 230 T€ | ca. 52 % | Nein – im Logistiksystem nicht mit den Aufträgen verbunden |
| Ungünstiger Produktmix | 150 T€ | ca. 34 % | Nein – Produktgruppe im zugänglichen Datennetz nicht vorhanden |
| Gestiegene Rabatte | 60 T€ | ca. 14 % | Ja – in den Vertriebsdaten sichtbar |
| **Gesamt** | **440 T€** | **100 %** | |

Die KI erkennt den Rabattanstieg und empfiehlt unter anderem, Konditionen mit Großkunden neu zu verhandeln. Der betroffene Kunde Nord erzielt 2,0 Mio. € Umsatz; die Expresslieferungen waren nicht durch ihn verursacht. Ohne Prüfung hätte eine plausible, aber unvollständige Erklärung damit eine unverhältnismäßige Maßnahme nahelegen können.

Der Fall verdeutlicht den Unterschied zwischen **Hinweis** und **Gesamterklärung**: Der Rabattanstieg war ein wahrer Hinweis, erklärte aber nur einen kleineren Teil der Differenz. Für eine allgemeine Auffälligkeitsanalyse kann das genügen, für eine konkrete Kundenmaßnahme nicht unbedingt.

## Formales Modell und wirtschaftliche Perspektive

### Datennetz

Die Arbeit modelliert ein Datennetz als gerichteten Multigraphen $G=(V,E)$:

- Knoten \(V\) repräsentieren Tabellen, Datensätze oder Dokumente mit Attributen, Qualitätsmerkmalen und Aktualität.
- Kanten \(E\) repräsentieren Joins, Mappings oder Transformationen, die Daten fachlich miteinander verbinden.
- Für eine Frage \(q\) benennt ein Domänenexperte die wesentlichen Einflussgrößen \(S_q\). Nur ein Teil davon kann im tatsächlich zugänglichen Netz beobachtbar sein.

Eine KI-Anwendung erzeugt auf Basis einer Frage und des zugänglichen Netzes eine Antwort. Die Arbeit unterscheidet dabei die tatsächlich verfügbare Datengrundlage von einer gedachten vollständigen Referenz. Das ist ein Modell zur strukturierten Diskussion von Abdeckung und Fehlerquellen, kein Beweis, dass sich jede reale Geschäftswahrheit vollständig erfassen lässt.

### Fehler und Error Budget

Die konzeptionelle Fehlerzerlegung unterscheidet:

- **fehlende Einflussgrößen** – wesentliche Treiber fehlen im genutzten Datennetz;
- **Definitionsabweichungen** – gleich benannte Kennzahlen haben verschiedene Bedeutungen;
- **zufällige Fehler** – beispielsweise durch Datenqualität oder Aktualisierungsverzögerungen.

Ein Error Budget beschreibt, welcher erwartete Verlust für eine konkrete Entscheidung noch akzeptabel ist. Die zentrale Bedingung lautet:

$$
\mathbb{E}[L(\hat y,y^*)] \leq \varepsilon W,
$$

wobei \(L\) den Verlust aus der Antwortabweichung, \(W\) die Stakes und \(\varepsilon\) den für den Anwendungsfall festgelegten Anteil bezeichnet. Die konkrete Verlustfunktion und Schwelle müssen fachlich bestimmt werden; die Formel setzt **keinen** universellen Schwellenwert fest.

### Abweichungen und Value of Information

Eine Abweichung zwischen der KI-Antwort und einer internen Analyse ist nicht automatisch ein Modellfehler. Sie kann auf fehlende Quellen oder Attribute, unklare Definitionen, veraltete Daten oder eine unvollständige eigene Analyse hinweisen. Die Arbeit beschreibt, wie dieser Befund in einen Kreislauf aus Prüfung, Verbesserung und erneuter Messung einfließen kann.

Die **Value of Information (VOI)** betrachtet, ob der erwartete zusätzliche Nutzen einer Datenintegration deren Kosten rechtfertigt. Das ist als Entscheidungsrahmen gedacht; eine belastbare Anwendung benötigt konkrete Annahmen zu Kosten, Nutzen, Unsicherheit und möglichen Handlungsalternativen.

## Vertrauensstufen

Die Arbeit unterscheidet vier stufenweise Nutzungsarten:

| Stufe | Rolle der KI | Typische Kontrolle |
|---|---|---|
| 1 | **Hinweis** | Eine Person prüft die angezeigte Auffälligkeit eigenständig. |
| 2 | **Gegenprüfung** | KI-Ergebnis und interne Analyse werden verglichen; Unterschiede werden untersucht. |
| 3 | **Vorbereitung von Entscheidungen** | Qualität, Quelle, Definition und Datenstichtag sind nachvollziehbar; ein Mensch entscheidet. |
| 4 | **Automatisierte Handlung** | Ausdrückliche Freigabe, hohe Zuverlässigkeit, Protokollierung und Eingriffsmöglichkeit sind erforderlich. |

Die Stufen sind keine automatisch verdienten Zertifizierungen und kein allgemeines Gütesiegel für ein Modell oder Data Product. Die Freigabe wird pro Anwendung anhand von Stakes, Testfällen, Datenlage und Aufsicht entschieden.

## Data Products und Verantwortlichkeiten

### Bestandteile eines Data Products

Das Beispiel „Sales Result 360“ bündelt die Datengrundlage für Fragen zu Umsatz, Marge und deren Einflussfaktoren:

1. **Daten und Granularität:** etwa eine Zeile je Auftragsposition, ergänzt um Kunde, Produkt, Zeit, Vertrieb, Lieferung, Fracht, Plan und Vorjahr.
2. **Meaning:** Kennzahlendefinitionen wie DB I und DB II, Synonyme wie „Marge“, Zurechnungsregeln für Fracht und Vergleichszeiträume.
3. **Label:** fachlicher Kontakt, Qualitäts- und Aktualitätsangaben, Zugriffsrechte, Version und bekannte Einschränkungen.

Eine festgelegte semantische Regel ersetzt nicht die technische Verknüpfung zwischen Quellsystemen. Für eine belastbare Margenanalyse braucht es sowohl verständliche Definitionen als auch passende, überprüfbare Datenbeziehungen.

### Drei Verantwortlichkeiten vor dem Go-live

| Rolle | Hauptverantwortung |
|---|---|
| **Data Owner** | Definiert fachliche Bedeutung, Kennzahlen, Ausnahmen und Synonyme. |
| **Data Product Owner** | Verantwortet Lieferung, Vollständigkeit, Aktualität, Prüfung und Berechtigungen des Data Products. |
| **Use-Case Owner** | Genehmigt die Anwendung, verantwortet Testfragen und Error Budget und legt fest, wann ein Mensch entscheidet. |

In einem kleineren Unternehmen kann eine Person mehrere Rollen ausüben. Die Entscheidungen und Zuständigkeiten sollten trotzdem explizit dokumentiert sein. Wenn nicht klar ist, wer Definition, Lieferung oder Freigabe verantwortet, fehlt eine wichtige Grundlage für den Go-live.

## Voraussetzungen

Für das Erstellen der PDF-Datei benötigt man:

- eine TeX-Distribution, beispielsweise [MiKTeX](https://miktex.org/) unter Windows oder [TeX Live](https://www.tug.org/texlive/) unter Linux/macOS;
- `latexmk`;
- den für das Dokument benötigten LaTeX-Paketbestand. Verwendet werden unter anderem `babel`, `lmodern`, `amsmath`, `amssymb`, `amsthm`, `geometry`, `graphicx`, `hyperref`, `booktabs`, `listings`, `xcolor`, `enumitem` und `microtype`.

Die Arbeit ist UTF-8-kodiert und mit `pdflatex`/`latexmk` aufgebaut. Für den Python-Code wird Python ab 3.11 benötigt, siehe [Software und Tests](#software-und-tests); für die PDF ist keine Python-Laufzeit nötig.

## PDF erstellen

Die folgenden Befehle verwenden PowerShell auf Windows.

### Build im Dokumentverzeichnis

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error science\aidataeco.tex
```

Dieser Befehl erzeugt die PDF-Datei und LaTeX-Hilfsdateien neben der Quelle unter `science\`. Die PDF-Datei ist versioniert; der Build kann daher eine bereits vorhandene Projekt-PDF ersetzen. Vor dem Bauen sollte `git status --short` geprüft und ein beabsichtigter PDF-Unterschied anschließend kontrolliert werden.

### Build in einem separaten Verzeichnis

Um die vorhandene PDF und die Quelle nicht mit lokalen Build-Ausgaben zu überschreiben, lässt sich ein separates Verzeichnis verwenden:

```powershell
$build = Join-Path $env:TEMP "aidataeco-build"
New-Item -ItemType Directory -Force -Path $build | Out-Null
latexmk -pdf -interaction=nonstopmode -halt-on-error "-outdir=$build" science\aidataeco.tex
```

Die erzeugte PDF liegt danach in `$build`. Das Build-Verzeichnis ist lokal und muss nicht zum Repository hinzugefügt werden.

### Linux und macOS

```bash
mkdir -p /tmp/aidataeco-build
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir=/tmp/aidataeco-build \
  science/aidataeco.tex
```

Wenn `latexmk` wegen fehlender TeX-Pakete abbricht, sind zuerst die in der Fehlermeldung genannten Pakete über die jeweilige TeX-Distribution zu installieren. Paketinstallation und TeX-Updates sind nicht Bestandteil des Repository-Builds.

### Build-Ausgaben

Ein typischer Build erzeugt `.aux`, `.fdb_latexmk`, `.fls`, `.log`, `.out` und `.toc`; je nach Editor und Optionen kann auch eine SyncTeX-Datei erzeugt werden. Die verlässliche Erfolgskontrolle ist der Exit-Code von `latexmk` und eine tatsächlich erzeugte, lesbare PDF. Warnungen zu Zeilenumbrüchen oder Sprachmustern sollten gesondert geprüft werden; sie sind nicht in jedem Fall Kompilierfehler.

## Prüfen und weiterentwickeln

Für den Python-Code gibt es Tests (siehe [Software und Tests](#software-und-tests)); für reine Änderungen an der Dokumentation gibt es keine automatisierten Dokumentationstests. Nach einer Änderung an der TeX-Quelle empfiehlt sich mindestens:

1. die PDF mit `latexmk -pdf -interaction=nonstopmode -halt-on-error ...` zu bauen;
2. den Build-Exit-Code zu kontrollieren;
3. die erzeugte PDF zu öffnen und Inhaltsverzeichnis, Tabellen, Formeln, Links und Literaturverzeichnis zu prüfen;
4. den LaTeX-Log auf unbeabsichtigte `Undefined control sequence`, ungelöste Referenzen, übervolle Zeilen und sonstige relevante Warnungen zu prüfen;
5. `git diff --check` und `git status --short` auszuführen;
6. Änderungen an der PDF nur dann einzuchecken, wenn sie zum aktualisierten Quelltext gehören und visuell geprüft wurden.

Ein projektbezogener Check des Arbeitsbaums:

```powershell
git diff --check
git status --short
```

### Wissenschaftliche und redaktionelle Änderungen

- Inhaltliche Aussagen sollten kenntlich machen, ob sie Definition, Modellannahme, illustrative Fallstudie oder empirischer Befund sind.
- Zahlen aus der Fallstudie nicht als unabhängig erhobene Unternehmensdaten darstellen.
- Die im Webinar genannten Umfragewerte als Angaben aus der Präsentation kennzeichnen; die Arbeit weist darauf hin, dass die genaue Zuordnung der Einzelwerte zu Quellen dort nicht näher aufgeschlüsselt ist.
- Neue Literaturangaben vollständig und konsistent im Text sowie im Literaturverzeichnis ergänzen.
- Aussagen zu Error Budgets, statistischer Zuverlässigkeit oder wirtschaftlichem Nutzen nicht allgemeiner formulieren, als es die zugrunde liegenden Annahmen erlauben.
- Änderungen an mathematischen Definitionen und Beweisen auch in den praktischen Beispielen, Messgrößen und Checklisten nachvollziehen.
- Bei überarbeiteten TeX-Abschnitten PDF-Lesezeichen, Umlaute, Sonderzeichen, mathematische Symbole und Tabellenumbrüche kontrollieren.

## Stand und Grenzen

Dieses Repository ist in erster Linie ein **wissenschaftliches Dokumentationsprojekt**. Der Code in `src/` setzt Definitionen und Kennzahlen der Arbeit als geprüfte Bausteine um und enthält ein Prüfwerkzeug für Freigabeberichte; er ist kein fertiges KI- oder Datenprodukt. Die formalen Modelle strukturieren die Argumentation; sie stellen weder ein zertifiziertes Messverfahren noch eine produktionsreife Governance-Lösung dar. Ein erfolgreicher Testlauf ist kein empirischer Wirksamkeitsnachweis und keine Freigabe für autonome Handlungen. Ebenso ist ein Freigabebericht ohne Hindernisse keine Freigabe, sondern nur die Feststellung, dass keine der formalisierten Bedingungen verletzt ist; organisatorische Nachweise werden erklärt, nicht überprüft.

Die Fallstudie ist illustrativ und wird auf das zugrunde liegende Webinar zurückgeführt. Die dort genannten Prozentwerte werden in der Arbeit als Präsentationsangaben gekennzeichnet und nicht als unabhängig verifizierte Primärerhebung ausgegeben. Für Entscheidungen in einem Unternehmen wären geeignete interne Daten, fachlich geprüfte Referenzfälle und eine nachvollziehbare Fehlerbewertung erforderlich.

Auch die vier Vertrauensstufen sind ein konzeptioneller Rahmen. Sie definieren keine branchenspezifische Norm, regulatorische Einstufung oder automatische Freigabe. Die Entscheidung über eine reale KI-Anwendung bleibt an den konkreten Stakes, den bekannten Einschränkungen und den zuständigen Personen auszurichten.

## Quellen und weiterführende Arbeiten

Die Arbeit führt die folgenden Quellen im Literaturverzeichnis:

1. **Michael Sullmann (BE-terna).** Webinar *Data Product and AI in Controlling*, Oktober 2026. Grundlage für die im Text als Webinar-Angaben gekennzeichneten Inhalte und die illustrative Fallstudie.
2. **Stephan Epp.** *Wirtschaftliche Konsequenzen eines effizienten SAT-Solvers*, 12. Oktober 2026. [Repository](https://github.com/naphz86/subgraph-sat-solver-econ).
3. **Stephan Epp.** *Wirtschaftssysteme unter Unsicherheit*, 3. September 2026. [Repository und Wissenschaftsordner](https://github.com/naphets86/odd/tree/main/science/uncrtecos).

Die Arbeiten [2] und [3] sind ergänzende wissenschaftliche Vorarbeiten des Autors. Ihre Nennung bedeutet nicht, dass die vorliegende Arbeit ein SAT-Solver- oder ein Wirtschaftssystem-Simulationspaket enthält.

## Software und Tests

`src/` setzt das Dokumentmodell als typisierte, exakt rechnende (`fractions.Fraction`) Python-Bausteine um. Fehlende Evidenz zählt nie als Erfolg: unbekannte Qualität, fehlende Provenance, unbeantwortete Testfragen und fehlende Verantwortliche werden als solche ausgewiesen, ungültige Eingaben lösen `ValueError` aus.

| Modul | Inhalt aus der Arbeit |
|---|---|
| `model` | Datennetz, Data Product, Label, Provenance, Antworten |
| `errorbudget` | Stakes, Error Budget, Fehlerzerlegung, Gut-genug-Bedingung |
| `diagnosis` | Abweichung als Bayes-Indikator, Lern-Loop, VOI-Bedingung, Abweichungsursachen |
| `governance` | Vertrauensstufen, drei Verantwortlichkeiten, Freigabehindernisse |
| `evaluation` | Bestehensquote, erklärter Anteil, Provenance-Abdeckung, Vollständigkeit, Aktualität |
| `integration` | Auswahl von Datenquellen unter Budget und Abhängigkeiten (Erweiterung der VOI-Bedingung) |
| `experiment` | reproduzierbares Protokoll von Eingaben, Konfiguration, Versionen, Resultaten |
| `casestudy` | illustrative Fallstudie zur sinkenden Marge mit den Zahlen der Arbeit |
| `parsing`, `spec` | strenges Einlesen von Spezifikation (JSON/YAML) und Antworten; messbare Nachweise dürfen nicht erklärt werden |
| `provider` | Schnittstelle zur KI-Anwendung für die Referenzfragen (`ProviderError` = keine Antwort) |
| `report` | Freigabebericht: abgeleitete Nachweise, Freigabehindernisse, Fingerprint, Markdown/JSON |
| `compare` | Regressionsvergleich zweier gespeicherter Berichte |
| `cli` | Kommandozeile `report` und `compare` |
| `web/` (eigenes Paket) | zustandslose FastAPI-JSON-API über allen Bausteinen, siehe [JSON-API](#json-api-fastapi) |

Die Verwendung der Module `spec`, `provider`, `report`, `compare` und `cli` (Spezifikation, Antworten, Freigabebericht, Monitoring) steht mit vielen Beispielen im Abschnitt [Prüfwerkzeug und Python-API](#prüfwerkzeug-und-python-api-operationalisierung).

### Wiederverwendung von subgraph-sat-solver-econ

Entscheider, Schaltkreisbausteine und die Formel der Rechenlücke werden nicht neu geschrieben, sondern aus [`subgraph-sat-solver-econ`](https://github.com/naphz86/subgraph-sat-solver-econ) importiert (`subgraph_sat_solver_econ`): `integration` formuliert nur das Problem und nutzt `Problem`, `maximize` und `DpllBackend`; `evaluation` berechnet den erklärten Anteil mit `computation_gap` und `total_output`. Die Abhängigkeit steht in `pyproject.toml`. Damit das Referenzprojekt unter diesem Namen importierbar ist, braucht es dort die Paketabbildung `package-dir = { subgraph_sat_solver_econ = "src" }` (siehe dessen `pyproject.toml`).

### Installieren und testen

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

`pytest` führt alle Tests aus (Bausteine in `src/`, Kommandozeile, README-Beispiele und JSON-API in `web/`) und erzeugt den Coverage-Bericht (Zeilen und Zweige für `src/` und `web/`) als HTML unter `doc/coverage/index.html`. Der Bericht ist ein Build-Artefakt und wird bei Bedarf neu erzeugt.

## Prüfwerkzeug und Python-API (Operationalisierung)

Dieser Abschnitt beschreibt, wie der Code zum Abschnitt „Operationalisierung“ der Arbeit verwendet wird: als **Python-API** (Bibliothek) und als **Kommandozeile**. Das Werkzeug prüft, ob ein Data Product für einen Anwendungsfall auf einer angestrebten Vertrauensstufe freigabereif ist, und liefert dazu einen **Freigabebericht**. Es entscheidet nicht selbst: Ein Bericht ohne Freigabehindernisse ist keine Freigabe, sondern nur die Feststellung, dass keine der formalisierten Bedingungen verletzt ist. Die Entscheidung trifft der Use-Case Owner.

Der Datenfluss ist immer derselbe:

```text
Spezifikation (YAML/JSON) ──load_spec────────► Spec ─────┐
Antworten der KI (JSON) ────answers_for──────► Answers ──┼──► build_report ──► GoLiveReport ──► to_markdown() / to_json()
Stichtag, erwarteter Verlust, Versionen ─────────────────┘                          │
                                                                                    ▼
                          gespeicherter Bericht (JSON) ──from_dict──► GoLiveReport ──► compare_reports ──► Comparison
```

Drei Grundsätze gelten durchgehend:

- **Messen statt Erklären:** Kennzahlen, Provenance, Qualität und Error Budget werden aus den Daten *abgeleitet*. In der Spezifikation erklärt werden nur organisatorische Nachweise (Mensch entscheidet, ausdrückliche Freigabe, Protokollierung, Eingriffspfad).
- **Fehlender Nachweis ist nie ein Erfolg:** Unbekannte Qualität, fehlende Provenance, unbeantwortete Fragen, unbekannte Aktualität und nicht benannte Verantwortliche erscheinen als Freigabehindernis.
- **Strenge Eingabe:** Unbekannte Felder, falsche Typen und ungültige Zahlen lösen `ValueError` aus. Nichts wird stillschweigend ignoriert. Alle Größen sind exakte `fractions.Fraction`; Brüche stehen in JSON als Text (`"3/20"`).

### API im Überblick

| Aufgabe | Funktion oder Klasse | Modul (`aidataeco.…`) |
|---|---|---|
| Datei lesen (`.json`, `.yaml`, `.yml`) | `read_document(pfad)` | `spec` |
| Spezifikation laden und prüfen | `load_spec(pfad)`, `parse_spec(mapping)` → `Spec` | `spec` |
| Antworten der KI einlesen | `answers_for(spec, mapping)`, `parse_answers(mapping)` | `spec` |
| Antworten selbst erzeugen | `Answer`, `Provenance` | `model` |
| KI-Anwendung anbinden | `AnswerProvider`, `StaticProvider`, `collect_answers`, `ProviderError` | `provider` |
| Bericht erstellen | `build_report(spec, answers, today, expected_loss=None, versions=None)` → `GoLiveReport` | `report` |
| Bericht ausgeben | `to_markdown()`, `to_json()`, `to_dict()` | `report` |
| Gespeicherten Bericht lesen | `GoLiveReport.from_dict(mapping)` | `report` |
| Berichte vergleichen | `compare_reports(alt, neu)` → `Comparison` | `compare` |
| Kommandozeile | `main(argv)`, `python -m aidataeco …` | `cli` |

Installiert wird mit `pip install -e ".[dev]"` (siehe [Installieren und testen](#installieren-und-testen)); der Importname ist `aidataeco`. YAML benötigt PyYAML (`pip install -e ".[yaml]"`, in `.[dev]` enthalten), JSON funktioniert ohne Zusatzpaket.

Die folgenden Beispiele bauen aufeinander auf und teilen sich eine Python-Sitzung. Die gezeigten Ausgaben sind echte Ausgaben; `tests/test_readme_examples.py` führt alle Beispiele aus und vergleicht die Ausgaben mit diesem Text. Pfade wie `examples/…` sind relativ zum Repository-Verzeichnis.

<!-- api-beispiele:start -->

### Schnellstart

```python
from datetime import date

from aidataeco.report import build_report
from aidataeco.spec import answers_for, load_spec, read_document

spec = load_spec("examples/sales_result_360.yaml")
answers = answers_for(spec, read_document("examples/answers_sales_result_360.json"))
today = date(2026, 10, 22)

report = build_report(spec, answers, today=today, expected_loss=380)

print("blockiert:", report.blocked, "| Hindernisse:", len(report.blockers))
for blocker in report.blockers:
    print("-", blocker)
```

```text
blockiert: True | Hindernisse: 7
- Nachweis fehlt: Zentrale Kennzahlen sind verknüpft und definiert
- Nachweis fehlt: Quelle, Definition und Zeitstempel sind verfügbar
- Nachweis fehlt: Qualität ist messbar
- Nachweis fehlt: Error Budget ist für den Anwendungsfall eingehalten
- Aktualität nicht belegt: freight
- Aktualität nicht belegt: products
- Bestehensquote liegt unter dem Mindestwert
```

Die Beispiel-Spezifikation gehört zur Fallstudie „Sinkende Marge“ der Arbeit: Das Netz ist für die Frage nicht ausreichend, und der Bericht zeigt genau, woran es fehlt. Der Bericht lässt sich als Markdown lesen:

```python
markdown = report.to_markdown().split("## Nachweise")[0]
print("\n".join(line for line in markdown.splitlines() if "Fingerprint" not in line))
```

```text
# Freigabebericht: Sales Result 360

- Version: 1.2, Owner: Leitung Controlling
- Angestrebte Stufe: 3 (DECISION_PREPARATION)
- Stichtag: 2026-10-22

## Ergebnis

**7 Freigabehindernis(se)** für Stufe 3.

- Nachweis fehlt: Zentrale Kennzahlen sind verknüpft und definiert
- Nachweis fehlt: Quelle, Definition und Zeitstempel sind verfügbar
- Nachweis fehlt: Qualität ist messbar
- Nachweis fehlt: Error Budget ist für den Anwendungsfall eingehalten
- Aktualität nicht belegt: freight
- Aktualität nicht belegt: products
- Bestehensquote liegt unter dem Mindestwert

## Kennzahlen

| Kennzahl | Wert |
|---|---|
| Bestehensquote | 1/6 (16,7 %) |
| Provenance-Abdeckung | 2/3 (66,7 %) |
| Unbeantwortete Fragen | 1 |
| Mindest-Bestehensquote | 3/4 (75,0 %) |
| Erwarteter Verlust | 380 |
| Zulässiger Verlust ε·W | 22 |
| Offene Verknüpfungen | 1 |
```

### Die Spezifikation

Eine Spezifikation beschreibt Datennetz, Data Product, Verantwortliche und Anwendungsfall. Sie liegt als YAML oder JSON vor; die Felder sind in beiden Formaten gleich. Auszug aus [`examples/sales_result_360.yaml`](examples/sales_result_360.yaml):

```yaml
network:                                  # das gesamte Datennetz (V, E)
  nodes:
    - name: orders
      attributes: [order_id, customer, product_id, revenue, discount]
      quality: "19/20"                    # optional; fehlt sie, ist die Qualität unbekannt
      updated: 2026-10-21                 # optional; fehlt es, ist die Aktualität unbekannt
    - name: freight
      attributes: [delivery_id, express_cost]
  edges:
    - {source: orders, target: products, transformation: "orders.product_id = products.product_id"}

product:                                  # das Data Product (V_P ⊆ V, E_P ⊆ E)
  name: Sales Result 360
  nodes: [orders, freight, products]
  edges:
    - {source: orders, target: products, transformation: "orders.product_id = products.product_id"}
  meaning:
    definitions: {DB II: DB I abzüglich Fracht und Vertriebseinzelkosten}
    synonyms: {Marge: DB II}
    rules: [Expressfracht wird der verursachenden Lieferung zugeordnet.]
  label: {owner: Leitung Controlling, version: "1.2", frequency_days: 7}
  required_links: [[orders, freight]]     # diese Knoten müssen verbunden sein
  kpis: [DB II, Marge]                    # diese Begriffe müssen definiert sein

accountabilities:                         # drei benannte Verantwortliche
  data_owner: Leitung Controlling
  data_product_owner: Datenteam
  use_case_owner: Fachbereich Vertrieb

use_case:
  level: DECISION_PREPARATION             # oder 1 bis 4
  error_budget: {stakes: 440, epsilon: "1/20"}   # zulässiger erwarteter Verlust: ε·W = 22
  min_pass_rate: "3/4"                    # optional
  reference_cases:                        # Referenzfragen mit Toleranz und Gewicht
    - {question: "…Expressfracht…?", reference: 230, tolerance: 10, weight: 3}

evidence:                                 # nur organisatorische Nachweise
  human_decides: true
```

| Abschnitt | Felder (`?` = optional) |
|---|---|
| `network` | `nodes[]`: `name`, `attributes?`, `quality?` (0 bis 1), `updated?` (Datum); `edges?[]`: `source`, `target`, `transformation` |
| `product` | `name`, `nodes[]`, `edges?[]` (müssen im Netz liegen), `meaning` (`definitions`, `synonyms?`, `rules?`), `label` (`owner`, `version` als Text, `frequency_days`, `quality?`), `required_links?`, `kpis?` |
| `accountabilities?` | `data_owner?`, `data_product_owner?`, `use_case_owner?` (nicht benannt = fehlt) |
| `use_case` | `level` (Name `HINT`, `CROSS_CHECK`, `DECISION_PREPARATION`, `AUTOMATED_ACTION` oder 1 bis 4), `error_budget?` (`stakes`, `epsilon`), `min_pass_rate?` (0 bis 1), `reference_cases?[]` (`question`, `reference`, `tolerance`, `weight?` = 1) |
| `evidence?` | `human_decides?`, `explicit_approval?`, `logging?`, `intervention_path?` (Standard jeweils `false`) |

Zahlen dürfen als Zahl oder als Text angegeben werden (`0.95`, `"19/20"`); Datumsangaben als `JJJJ-MM-TT`. Das geprüfte Objekt `Spec` enthält die Bausteine der Arbeit:

```python
print(spec.product.name, spec.product.label.version)
print(spec.use_case.level.name, spec.use_case.budget.limit)
print(sorted(spec.product.node_names))
print(spec.required_links)
print([str(case.weight) for case in spec.use_case.cases])
print(spec.product.meaning.resolve("Marge"))
print(spec.accountabilities.missing())
```

```text
Sales Result 360 1.2
DECISION_PREPARATION 22
['freight', 'orders', 'products']
(('orders', 'freight'),)
['3', '2', '1']
DB I abzüglich Fracht und Vertriebseinzelkosten
()
```

#### Spezifikation aus einem Python-Dict

`parse_spec` nimmt jedes Mapping, also auch ein Dict, das Sie selbst bauen oder aus einer Datenbank lesen. Die kleinste gültige Spezifikation braucht Netz, Data Product und die Stufe:

```python
import copy

from aidataeco.spec import parse_spec

minimal = {
    "network": {"nodes": [{"name": "orders", "attributes": ["order_id", "revenue"]}]},
    "product": {
        "name": "Orders",
        "nodes": ["orders"],
        "meaning": {"definitions": {"Umsatz": "Summe der Nettoerlöse"}},
        "label": {"owner": "Vertrieb", "version": "0.1", "frequency_days": 1},
    },
    "use_case": {"level": "HINT"},
}

hint = build_report(parse_spec(minimal), [], today)
print(hint.blockers)
```

```text
('Keine verantwortliche Person benannt: Data Owner', 'Keine verantwortliche Person benannt: Data Product Owner', 'Keine verantwortliche Person benannt: Use-Case Owner')
```

Verantwortliche werden nie vorbelegt. Erst wenn alle drei benannt sind, steht auf Stufe 1 nichts mehr im Weg:

```python
minimal["accountabilities"] = {
    "data_owner": "Vertrieb",
    "data_product_owner": "Datenteam",
    "use_case_owner": "Vertriebsleitung",
}
print(build_report(parse_spec(minimal), [], today).blockers)
```

```text
()
```

#### Ungültige Spezifikationen

Fehler werden mit dem Feldnamen gemeldet. Die Meldungen sind auf Deutsch und lösen `ValueError` aus:

```python
def try_spec(change):
    data = copy.deepcopy(minimal)
    change(data)
    try:
        parse_spec(data)
    except ValueError as error:
        print("Fehler:", error)

try_spec(lambda d: d.update(evidenz={}))                                # Tippfehler im Feldnamen
try_spec(lambda d: d.update(evidence={"provenance_available": True}))   # messbar, nicht erklärbar
try_spec(lambda d: d["product"]["label"].update(version=0.1))           # Zahl statt Text
try_spec(lambda d: d["use_case"].update(level="HOCH"))                  # unbekannte Stufe
try_spec(lambda d: d["use_case"].update(level=5))                       # Stufe außerhalb 1 bis 4
try_spec(lambda d: d["use_case"].update(min_pass_rate=2))               # Quote außerhalb [0, 1]
try_spec(lambda d: d["product"].update(nodes=["orders", "fehlt"]))      # Knoten nicht im Netz
```

```text
Fehler: Spezifikation: Unbekannte Felder: evidenz
Fehler: evidence: wird aus den Daten gemessen und darf nicht erklärt werden: provenance_available
Fehler: product.label.version muss ein Text sein (in YAML ggf. in Anführungszeichen setzen)
Fehler: use_case.level: Unbekannte Stufe 'HOCH'
Fehler: use_case.level: Stufe muss 1 bis 4 sein, nicht 5
Fehler: use_case.min_pass_rate muss in [0, 1] liegen
Fehler: V_P muss eine Teilmenge von V sein
```

### Antworten der KI

Die Antworten stehen als JSON (oder YAML) je Referenzfrage. `value` ist die Antwortzahl oder `null` für „keine Antwort“; `provenance` ist optional und beschreibt Quellen (`[Name, Version]`), den Datenstichtag und die angewendeten Regeln:

```python
raw_answers = read_document("examples/answers_sales_result_360.json")
freight_q, mix_q, discount_q = (case.question for case in spec.use_case.cases)

print(raw_answers[discount_q])
```

```text
{'value': 60, 'provenance': {'sources': [['orders', '1.2']], 'cutoff': '2026-10-21', 'rules': ['Rabattquote']}}
```

`answers_for` ordnet die Antworten den Referenzfällen zu und liefert ein Tupel von `Answer` in der Reihenfolge der Fälle. Eine Frage ohne Antwort gilt als unbeantwortet; eine Antwort zu einer Frage, die kein Referenzfall kennt (meist ein Tippfehler), ist ein Fehler:

```python
print([str(answer.value) for answer in answers])

without_discount = {q: a for q, a in raw_answers.items() if q != discount_q}
print(answers_for(spec, without_discount)[2])

try:
    answers_for(spec, {**raw_answers, "Welche Rabatte?": {"value": 1}})
except ValueError as error:
    print("Fehler:", error)
```

```text
['0', 'None', '60']
Answer(value=None, provenance=None)
Fehler: Antworten zu unbekannten Fragen: Welche Rabatte?
```

#### Antworten selbst erzeugen

Statt einer Datei kann jede Quelle `Answer`-Objekte liefern, zum Beispiel ein Skript, das die KI-Anwendung abfragt. `Provenance` ist vollständig, wenn mindestens eine Quelle, ein Datenstichtag und eine angewendete Regel vorliegen:

```python
from aidataeco.model import Answer, Provenance

provenance = Provenance(
    sources=(("orders", "1.2"), ("freight", "1.2")),
    cutoff=date(2026, 10, 21),
    rules=("DB II",),
)
own_answers = (Answer(230, provenance), Answer(150, provenance), Answer(60, provenance))

own_report = build_report(spec, own_answers, today, expected_loss=20)
print(own_report.evaluation)
print(provenance.is_complete(), Provenance().missing())
```

```text
Evaluation(pass_rate=Fraction(1, 1), provenance_coverage=Fraction(1, 1), unanswered=0)
True ('Quelle', 'Datenstichtag', 'Definition')
```

### Bericht erstellen und lesen

`build_report(spec, answers, today, expected_loss=None, versions=None)` ist eine reine Funktion: Gleiche Eingaben ergeben denselben Bericht. Der Stichtag `today` ist ein Parameter und wird nie aus der Systemuhr gelesen. Der `GoLiveReport` ist ein unveränderliches Objekt:

```python
for node in report.nodes:
    print(node.name, node.quality, node.updated, node.fresh)

print(report.evaluation)
print(report.missing_links)
print(report.expected_loss, report.budget_limit)
print(report.evidence)
```

```text
freight 4/5 2026-10-01 False
orders 19/20 2026-10-21 True
products None None None
Evaluation(pass_rate=Fraction(1, 6), provenance_coverage=Fraction(2, 3), unanswered=1)
(('orders', 'freight'),)
380 22
Evidence(kpis_defined=False, provenance_available=False, quality_measurable=False, error_budget_met=False, human_decides=True, explicit_approval=False, logging=False, intervention_path=False)
```

| Feld | Bedeutung |
|---|---|
| `blocked`, `blockers` | `True`, wenn mindestens ein Freigabehindernis besteht; die Hindernisse als Texte |
| `level`, `today`, `product`, `version`, `owner` | Angestrebte Stufe, Stichtag und Angaben des Data Products |
| `nodes` | je Knoten von `V_P`: `quality`, `updated`, `fresh` (`None` = Aktualität unbekannt) |
| `missing_links` | geforderte Verknüpfungen, die im Data Product nicht verbunden sind |
| `evaluation` | `pass_rate`, `provenance_coverage`, `unanswered`; `None` ohne Referenzfragen |
| `evidence` | die acht Nachweise (`True` = belegt) |
| `expected_loss`, `budget_limit` | übergebener erwarteter Verlust und zulässiger Verlust ε·W |
| `versions`, `fingerprint` | Python- und Paketversionen; SHA-256 der Eingaben |

Welche Nachweise gemessen und welche erklärt werden, und wann ein Freigabehindernis entsteht:

| Nachweis (`evidence`) | Quelle | Bedingung für „belegt“ |
|---|---|---|
| `kpis_defined` | gemessen | `kpis` nicht leer, alle `required_links` im Data Product verbunden, jeder Begriff in `meaning` definiert (auch über Synonym) |
| `provenance_available` | gemessen | mindestens eine Referenzfrage, und jede Antwort hat vollständige Provenance |
| `quality_measurable` | gemessen | `V_P` nicht leer und `quality` aller Knoten bekannt |
| `error_budget_met` | gemessen | `error_budget` angegeben, `expected_loss` übergeben und `expected_loss ≤ ε·W` |
| `human_decides`, `explicit_approval`, `logging`, `intervention_path` | erklärt | Wert in `evidence` der Spezifikation |

| Stufe | Anforderungen |
|---|---|
| alle | drei Verantwortliche benannt; `min_pass_rate` (falls angegeben) erreicht |
| 2 `CROSS_CHECK` | `kpis_defined` |
| 3 `DECISION_PREPARATION` | zusätzlich `provenance_available`, `quality_measurable`, `error_budget_met`, `human_decides`; jeder Knoten von `V_P` aktuell |
| 4 `AUTOMATED_ACTION` | zusätzlich `explicit_approval`, `logging`, `intervention_path`; `human_decides` entfällt |

Ein Knoten ist aktuell, wenn `updated` bekannt ist und höchstens `frequency_days` Tage vor dem Stichtag liegt; ein Datum in der Zukunft gilt als nicht aktuell.

### Error Budget und erwarteter Verlust

Das Werkzeug **schätzt den erwarteten Verlust nicht**, sondern erwartet ihn als Eingabe `expected_loss` (E[L(ŷ, y\*)] aus der Arbeit). Ohne ihn gilt das Error Budget als nicht belegt. Das Modul `errorbudget` hilft bei der Berechnung und der Gut-genug-Bedingung `E[L] ≤ ε·W`:

```python
from aidataeco.errorbudget import is_good_enough, linear_loss

loss = linear_loss(cost_per_unit=1, expected_abs_error=380)   # c · E|ŷ − y*|
print(loss, spec.use_case.budget.limit, is_good_enough(loss, spec.use_case.budget))

for value in (None, 22, 23):
    check_report = build_report(spec, answers, today, expected_loss=value)
    print(value, check_report.evidence.error_budget_met)
```

```text
380 22 False
None False
22 True
23 False
```

Ein erwarteter Verlust ohne `error_budget` in der Spezifikation, ein negativer Verlust und Antworten ohne Referenzfragen sind Eingabefehler (`ValueError`).

### Ausgabeformate

```python
from pathlib import Path

Path("reports").mkdir(exist_ok=True)
Path("reports/bericht.md").write_text(report.to_markdown(), encoding="utf-8")
Path("reports/bericht.json").write_text(report.to_json(), encoding="utf-8")

data = report.to_dict()
print(sorted(data))
print(data["level"], data["blocked"], data["expected_loss"])
print(data["evaluation"])
print(report.to_json().splitlines()[:3])
```

```text
['blocked', 'blockers', 'budget_limit', 'evaluation', 'evidence', 'expected_loss', 'fingerprint', 'level', 'min_pass_rate', 'missing_links', 'nodes', 'owner', 'product', 'today', 'version', 'versions']
DECISION_PREPARATION True 380
{'pass_rate': '1/6', 'provenance_coverage': '2/3', 'unanswered': 1}
['{', '  "blocked": true,', '  "blockers": [']
```

`to_json()` ist kanonisch (sortierte Schlüssel, Brüche als Text) und eignet sich zum Archivieren und für das [Monitoring](#monitoring-berichte-speichern-und-vergleichen). `to_dict()` liefert dieselben Daten als JSON-fähiges Dict.

### Stufen durchspielen

Dieselbe Spezifikation auf verschiedenen Stufen zeigt, wie die Anforderungen wachsen. Das Hilfsprogramm `check` baut aus Dicts einen Bericht und wird in den folgenden Beispielen wiederverwendet:

```python
from aidataeco.spec import parse_spec

def check(data, raw, when=today, loss=None):
    """Spezifikation und Antworten (Dicts) prüfen: parse_spec, answers_for, build_report."""
    parsed = parse_spec(data)
    return build_report(parsed, answers_for(parsed, raw), when, loss)

raw_spec = read_document("examples/sales_result_360.yaml")

for level in (1, 2, 3, 4):
    data = copy.deepcopy(raw_spec)
    data["use_case"]["level"] = level
    print("Stufe", level, "->", len(check(data, raw_answers, loss=380).blockers), "Hindernisse")
```

```text
Stufe 1 -> 1 Hindernisse
Stufe 2 -> 2 Hindernisse
Stufe 3 -> 7 Hindernisse
Stufe 4 -> 10 Hindernisse
```

Mit steigender Stufe kommen Anforderungen hinzu, und bestehende Hindernisse verschwinden nicht. Einzige Ausnahme ist die Aufsichtsforderung `human_decides`: Sie gilt nur auf Stufe 3 und wird auf Stufe 4 durch Freigabe, Protokollierung und Eingriffspfad ersetzt (Satz zur Stufenmonotonie in der Arbeit). Deshalb hat Stufe 4 hier mehr Hindernisse als Stufe 3.

### Freigabereife herstellen

Der Bericht ist eine Arbeitsliste. Die folgenden Schritte beheben die sieben Hindernisse der Beispiel-Spezifikation nacheinander:

```python
data = copy.deepcopy(raw_spec)
new_answers = copy.deepcopy(raw_answers)
print("Ausgangslage:", len(check(data, new_answers, loss=380).blockers))

# 1. Verknüpfung zwischen Auftrag und Fracht herstellen (Kante im Netz und im Data Product)
edge = {"source": "orders", "target": "freight",
        "transformation": "orders.delivery_id = freight.delivery_id"}
data["network"]["edges"].append(edge)
data["product"]["edges"].append(edge)
print("1. Verknüpfung:", len(check(data, new_answers, loss=380).blockers))

# 2. Aktualität und Qualität aller Knoten belegen
for node in data["network"]["nodes"]:
    node["updated"] = "2026-10-21"
    node.setdefault("quality", "9/10")
print("2. Aktualität und Qualität:", len(check(data, new_answers, loss=380).blockers))

# 3. Bessere Antworten mit vollständiger Provenance
sources = {"sources": [["orders", "1.2"], ["freight", "1.2"]], "cutoff": "2026-10-21", "rules": ["DB II"]}
new_answers[freight_q] = {"value": 228, "provenance": sources}
new_answers[mix_q] = {"value": 148, "provenance": sources}
print("3. Antworten:", len(check(data, new_answers, loss=380).blockers))

# 4. Erwarteter Verlust innerhalb des Error Budgets (ε·W = 22)
ready = check(data, new_answers, loss=20)
print("4. Error Budget:", len(ready.blockers), "| blockiert:", ready.blocked)
```

```text
Ausgangslage: 7
1. Verknüpfung: 6
2. Aktualität und Qualität: 3
3. Antworten: 1
4. Error Budget: 0 | blockiert: False
```

Ein leerer `blockers`-Wert ist immer noch keine Freigabe; er sagt nur, dass keine der formalisierten Bedingungen verletzt ist.

### Monitoring: Berichte speichern und vergleichen

Berichte werden als JSON archiviert, später wieder gelesen und verglichen. Der Vergleich ist exakt (ohne Toleranz); fehlender Nachweis gilt als schlechter als jeder Wert. Eine *Regression* liegt vor, wenn sich eine Kennzahl verschlechtert oder ein Freigabehindernis neu hinzukommt:

```python
from aidataeco.compare import compare_reports
from aidataeco.report import GoLiveReport

old_report = check(raw_spec, raw_answers, loss=380)
Path("reports/2026-10-22.json").write_text(old_report.to_json(), encoding="utf-8")

stored = GoLiveReport.from_dict(read_document("reports/2026-10-22.json"))
print("Archiv verlustfrei:", stored == old_report)

comparison = compare_reports(stored, ready)
print("Regression:", comparison.has_regression)
print("Behobene Hindernisse:", len(comparison.resolved_blockers), "| neue:", comparison.new_blockers)
for change in comparison.changes:
    print(f"{change.metric}: {change.before} -> {change.after} ({change.direction.value})")
```

```text
Archiv verlustfrei: True
Regression: False
Behobene Hindernisse: 7 | neue: ()
Bestehensquote: 1/6 -> 1 (verbessert)
Provenance-Abdeckung: 2/3 -> 1 (verbessert)
Unbeantwortete Fragen: 1 -> 0 (verbessert)
Offene Verknüpfungen: 1 -> 0 (verbessert)
Knoten ohne Aktualitätsnachweis: 2 -> 0 (verbessert)
Knoten ohne bekannte Qualität: 1 -> 0 (verbessert)
Freigabehindernisse: 7 -> 0 (verbessert)
```

Dieselben Eingaben werden mit der Zeit schlechter, weil die Aktualität verfällt. Das erkennt der Vergleich als Regression:

```python
later = check(data, new_answers, when=date(2026, 11, 25), loss=20)
regression = compare_reports(ready, later)
print(regression.has_regression)
print([change.metric for change in regression.regressions])
for blocker in regression.new_blockers:
    print("-", blocker)
```

```text
True
['Knoten ohne Aktualitätsnachweis', 'Freigabehindernisse']
- Aktualität nicht belegt: freight
- Aktualität nicht belegt: orders
- Aktualität nicht belegt: products
```

`comparison.to_markdown()` und `comparison.to_json()` liefern den Vergleich als Text. Berichte verschiedener Data Products sind nicht vergleichbar (`ValueError`). Der Vergleich der Bestehensquote ist nur sinnvoll, wenn die Referenzfragen gleich geblieben sind; `comparison.fingerprint_changed` zeigt, ob sich Eingaben geändert haben. Ein Bericht wird strikt zurückgelesen: unbekannte Felder oder ein `blocked`, das nicht zu `blockers` passt, lösen `ValueError` aus.

### Reproduzierbarkeit und Fingerprint

Der `fingerprint` bindet Spezifikation, Antworten, Stichtag, erwarteten Verlust und Versionen; das Ergebnis geht nicht ein. Gleiche Eingaben ergeben denselben Bericht und denselben Fingerprint. Für vergleichbare Läufe auf verschiedenen Rechnern können die Versionen fest vorgegeben werden:

```python
versions = {"python": "3.12.1"}
first = build_report(spec, answers, today, 380, versions)
second = build_report(spec, answers, today, 380, versions)
other_day = build_report(spec, answers, date(2026, 10, 23), 380, versions)

print(first.fingerprint == second.fingerprint, first.to_json() == second.to_json())
print(first.fingerprint == other_day.fingerprint)
print(len(first.fingerprint))
```

```text
True True
False
64
```

### Bausteine einzeln verwenden

Die Berichtsfunktion setzt nur bekannte Bausteine zusammen. Jeder lässt sich einzeln nutzen:

```python
from aidataeco.evaluation import evaluate, is_fresh
from aidataeco.governance import Accountabilities, Evidence, ReliabilityLevel, release_blockers

print(evaluate(spec.use_case.cases, answers))
print(is_fresh(date(2026, 10, 21), 7, today), is_fresh(None, 7, today))

evidence = Evidence(kpis_defined=True, provenance_available=True,
                    quality_measurable=True, error_budget_met=True)
roles = Accountabilities("Controlling", "Datenteam", "Vertrieb")
print(release_blockers(ReliabilityLevel.DECISION_PREPARATION, roles, evidence))
print(release_blockers(ReliabilityLevel.CROSS_CHECK, roles, Evidence()))
```

```text
Evaluation(pass_rate=Fraction(1, 6), provenance_coverage=Fraction(2, 3), unanswered=1)
True False
['Nachweis fehlt: Ein Mensch entscheidet']
['Nachweis fehlt: Zentrale Kennzahlen sind verknüpft und definiert']
```

### KI-Anwendung anbinden

Der Kern kennt keine konkrete KI. Ein **Adapter** ist eine Funktion `Frage -> Answer` (`AnswerProvider`). `collect_answers` stellt jede Referenzfrage genau einmal und liefert die Antworten in der Reihenfolge der Referenzfälle. Kann der Adapter keine Antwort liefern, löst er `ProviderError` aus; das zählt als „keine Antwort“, nie als Erfolg. Jede andere Ausnahme ist ein Programmfehler und wird nicht verschluckt:

```python
from aidataeco.provider import ProviderError, StaticProvider, collect_answers

def my_ai(question: str) -> Answer:
    if "Expressfracht" in question:
        return Answer(228, provenance)
    if "Produktmix" in question:
        raise ProviderError("Zeitüberschreitung")    # zählt als unbeantwortet
    return Answer(61, provenance)

ki_answers = collect_answers(spec.use_case.cases, my_ai)
print([str(answer.value) for answer in ki_answers])

ki_report = build_report(spec, ki_answers, today)
print(ki_report.evaluation)
```

```text
['228', 'None', '61']
Evaluation(pass_rate=Fraction(2, 3), provenance_coverage=Fraction(2, 3), unanswered=1)
```

`StaticProvider` liefert feste Antworten je Frage, etwa aus einer Datei oder in Tests; fehlt eine Frage, wird `ProviderError` ausgelöst und sie gilt als unbeantwortet:

```python
static = StaticProvider({discount_q: Answer(60, provenance)})
print([str(answer.value) for answer in collect_answers(spec.use_case.cases, static)])
```

```text
['None', 'None', '60']
```

Ein Adapter für einen HTTP-Dienst oder einen MCP-Server übersetzt Netzwerkfehler in `ProviderError` und bildet das Antwortformat der KI-Anwendung auf `Answer` ab (das Beispiel wird nicht ausgeführt, die Adresse und das Antwortformat sind Platzhalter):

```python skip
import json
import urllib.error
import urllib.request

from aidataeco.model import Answer, Provenance
from aidataeco.provider import ProviderError

def http_ai(question: str) -> Answer:
    request = urllib.request.Request(
        "https://ki.example.org/ask",
        data=json.dumps({"question": question}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            reply = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise ProviderError(str(error)) from error
    if reply.get("value") is None:
        return Answer(None)
    return Answer(reply["value"], Provenance(
        sources=tuple(tuple(source) for source in reply["sources"]),
        cutoff=date.fromisoformat(reply["cutoff"]),
        rules=tuple(reply["rules"]),
    ))
```

Ein Qualitäts-Gate in einer Testsuite oder Pipeline prüft, dass ein Data Product freigabereif bleibt (das Beispiel wird nicht ausgeführt):

```python skip
def test_sales_result_360_has_no_release_blockers():
    spec = load_spec("spezifikationen/sales_result_360.yaml")
    answers = collect_answers(spec.use_case.cases, http_ai)
    report = build_report(spec, answers, date.today(), expected_loss=measured_loss())
    assert not report.blocked, "\n".join(report.blockers)
```

<!-- api-beispiele:end -->

### Kommandozeile

Dieselbe Funktionalität steht ohne Python-Code zur Verfügung: als `python -m aidataeco …` oder, nach der Installation, als Befehl `aidataeco …`.

```bash
# Bericht erstellen: Markdown auf der Standardausgabe
python -m aidataeco report examples/sales_result_360.yaml \
    --answers examples/answers_sales_result_360.json --today 2026-10-22 --expected-loss 380

# Bericht als JSON archivieren
python -m aidataeco report examples/sales_result_360.yaml \
    --answers examples/answers_sales_result_360.json --today 2026-10-22 --expected-loss 380 \
    --format json --output bericht-2026-10.json

# Zwei archivierte Berichte vergleichen (Monitoring über die Zeit)
python -m aidataeco compare bericht-2026-09.json bericht-2026-10.json --format json
```

| Befehl und Option | Bedeutung |
|---|---|
| `report SPEC` | Spezifikation (`.json`, `.yaml`, `.yml`) prüfen und Bericht erstellen |
| `--answers DATEI` | Antworten je Referenzfrage; ohne Datei gilt jede Frage als unbeantwortet |
| `--today JJJJ-MM-TT` | Stichtag; Standard ist das heutige Datum (für reproduzierbare Läufe angeben) |
| `--expected-loss ZAHL` | erwarteter Verlust, exakt (`380`, `3/2`, `0.5`); ohne ihn ist das Error Budget nicht belegt |
| `compare ALT NEU` | zwei mit `--format json` gespeicherte Berichte desselben Data Products vergleichen |
| `--format markdown\|json` | Ausgabeformat, Standard `markdown` (bei beiden Befehlen) |
| `--output DATEI` | Ausgabe in Datei statt auf die Standardausgabe |

Exit-Codes: `0` kein Freigabehindernis bzw. keine Regression, `1` Freigabehindernis bzw. Regression, `2` ungültige Eingabe (Meldung auf der Fehlerausgabe). Damit lässt sich der Bericht als Gate in eine Pipeline einbinden:

```bash
python -m aidataeco report spezifikation.yaml --answers antworten.json --expected-loss 20 \
    --format json --output bericht.json
status=$?
if [ "$status" -eq 2 ]; then echo "Eingabefehler"; exit 2; fi
python -m aidataeco compare vorheriger-bericht.json bericht.json || { echo "Regression"; exit 1; }
exit "$status"
```

Der Aufruf aus Python entspricht `aidataeco.cli.main([...])` und liefert den Exit-Code als Rückgabewert.

### Häufige Fehlermeldungen

| Meldung (Auszug) | Ursache |
|---|---|
| `Unbekannte Felder: …` | Tippfehler oder nicht vorgesehenes Feld; erlaubt sind nur die Felder der Tabelle oben |
| `Pflichtfeld fehlt: …` | ein vorgeschriebenes Feld fehlt, zum Beispiel `use_case.level` |
| `… wird aus den Daten gemessen und darf nicht erklärt werden` | `evidence` enthält einen messbaren Nachweis |
| `… muss ein Text sein` | Zahl statt Text, etwa `version: 1.2`; in YAML in Anführungszeichen setzen (`"1.2"`) |
| `… ist keine gültige Zahl` | Zahl oder Bruch nicht lesbar (`"3/0"`, `"viel"`) |
| `… ist kein Datum (JJJJ-MM-TT)` | Datum nicht im ISO-Format |
| `Unbekannte Stufe …` / `Stufe muss 1 bis 4 sein` | `use_case.level` ungültig |
| `Antworten zu unbekannten Fragen: …` | Antwort-Schlüssel stimmt mit keiner Referenzfrage überein |
| `Antworten ohne Referenzfälle in der Spezifikation` | Antworten übergeben, aber `reference_cases` leer |
| `Erwarteter Verlust ohne Error Budget in der Spezifikation` | `expected_loss` übergeben, aber `use_case.error_budget` fehlt |
| `Berichte verschiedener Data Products sind nicht vergleichbar` | `compare_reports` mit Berichten zu verschiedenen Produkten |
| `YAML benötigt PyYAML` | `pip install -e ".[yaml]"` |

### Grenzen des Prüfwerkzeugs

- Die Prüfung ist nur so gut wie ihre Eingaben: Erklärte organisatorische Nachweise werden nicht überprüft, und Provenance ist nur formal vollständig, nicht inhaltlich richtig.
- Aktualität wird allein aus den angegebenen Aktualisierungsdaten abgeleitet.
- Der erwartete Verlust wird geliefert, nicht geschätzt.
- Der Vergleich kennt keine Toleranz und kein Messrauschen; die Bestehensquote ist nur bei unveränderten Referenzfragen vergleichbar.
- Konkrete KI-Adapter (etwa MCP) sind bewusst nicht Teil des Kerns. Die Web-Schicht (FastAPI) liegt getrennt in `web/` und ruft nur die öffentlichen Funktionen aus `src/` auf.
- Die Stufen sind ein konzeptioneller Rahmen und keine Norm; ein Bericht ohne Hindernisse ist keine Freigabe.

Die Definitionen und Beweise zu Freigabehindernissen, Antitonie, Stufenmonotonie, Reproduzierbarkeit und Regressionsvergleich stehen in der Arbeit im Abschnitt „Operationalisierung“.

## JSON-API (FastAPI)

`web/` stellt alle Bausteine als zustandslose JSON-API bereit (Version 2.0.0, identisch mit der Projektversion in der `pyproject.toml`). Jede Anfrage enthält ihre Eingaben vollständig, auch den Stichtag; es gibt keine Sitzung, keinen serverseitigen Zustand und keinen Zugriff auf die Systemuhr. Alle Rechnungen sind exakt (Brüche). `src/` wird dafür nicht verändert.

Nach der Installation (`pip install -e ".[dev]"`, siehe [Installieren und testen](#installieren-und-testen)) startet der Server mit Uvicorn:

```bash
uvicorn web.api:app --reload
```

Alternativ startet `aidataeco-api` den Server ohne Reload. Standardmäßig lauscht er auf `127.0.0.1:8000`; Host und Port lassen sich über `AIDATAECO_API_HOST` und `AIDATAECO_API_PORT` setzen. Die interaktive OpenAPI-Dokumentation liegt unter `http://127.0.0.1:8000/docs`.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/reports \
  -H 'Content-Type: application/json' \
  -d '{"spec": {...}, "answers": {...}, "today": "2026-10-22", "expected_loss": 5}'
```

Die Endpunkte (Präfix `/api/v1`):

| Endpunkt | Aufgabe |
|---|---|
| `GET /health`, `GET /options` | Status; Stufen, Nachweise, Abweichungsursachen und Eingabegrenzen |
| `POST /specs/validate` | Spezifikation streng lesen und zusammenfassen |
| `POST /reports`, `/reports/markdown` | Freigabebericht als JSON (wie `aidataeco report --format json`) oder Markdown |
| `POST /reports/cases` | Antworten je Referenzfrage auswerten (Bestehen, Provenance) |
| `POST /reports/compare`, `/reports/compare/markdown` | zwei Berichte vergleichen; Regression ja oder nein |
| `POST /evaluation/pass-rate`, `/explained-share`, `/completeness`, `/freshness` | Bestehensquote, erklärter Anteil, Vollständigkeit, Aktualität |
| `POST /error-budget/check`, `/linear-loss`, `/decomposition`, `/missing-bias`, `/lipschitz-bound` | Gut-genug-Bedingung, Fehlerzerlegung, Schranken |
| `POST /diagnosis/posterior`, `/bayes-update`, `/voi`, `/deviations`; `GET /diagnosis/causes` | Bayes-Indikator, Lern-Loop, VOI-Bedingung, Abweichungsursachen |
| `GET /governance/levels`; `POST /governance/blockers` | Vertrauensstufen und Freigabehindernisse |
| `POST /integration/select` | Datenquellen unter Budget und Abhängigkeiten auswählen (höchstens 10 Optionen) |
| `POST /experiments/fingerprint`; `GET /experiments/versions` | Experimentprotokoll und Versionen |
| `GET /case-study` | Fallstudie „Warum sinkt die Marge?“ |

Zahlen sind JSON-Zahlen oder Texte (`"3/20"`, `"0.15"`); Ergebnisse stehen als Bruch-Text. Spezifikation, Antworten und Berichte haben dieselben Schlüssel wie die Dateien der Kommandozeile. Ungültige Eingaben beantwortet die API mit HTTP 422 und `{"error":{"type":"input_error","message":"..."}}`, ungültige Feldtypen im FastAPI-Schema `detail`; Anfragen über der Größengrenze (`AIDATAECO_API_MAX_BODY_BYTES`, Standard 1 MiB) mit HTTP 413 und einen Solver-Ausfall mit HTTP 503. Für einen reproduzierbaren Fingerprint im Bericht `versions` mitgeben. Ein Bericht ohne Freigabehindernisse ist auch hier keine Freigabe. Weitere Einzelheiten und die Testübersicht stehen in [`web/README.md`](web/README.md).

## Erwerb

Der Preis für diese Software beträgt 27.145.000,00 EUR.

### Zahlungsinformationen

Name: Stephan Epp  
IBAN: DE24 5003 1900 0012 5603 20  
BIC: BBVADEFFXXX
