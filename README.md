# Wann ist das Datennetz gut genug für KI?

**Ein ökonomischer und formaler Ansatz zur verantwortbaren Nutzung von KI in Unternehmen**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-181%20passed-4c1)](tests/)
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-100%25-brightgreen)](doc/coverage/index.html)
[![scicov](https://img.shields.io/badge/scicov-10-ff69b4)](doc/coverage/index.html)

Dieses Repository enthält eine wissenschaftliche Arbeit über die Frage, wann das Datennetz eines Unternehmens für eine bestimmte KI-Anwendung gut genug ist. Im Mittelpunkt steht nicht die Suche nach fehlerfreien Daten oder einem perfekten Modell. Entscheidend ist, ob die verbleibende Unsicherheit für den jeweiligen Zweck und die möglichen Folgen einer Entscheidung vertretbar ist.

Die Arbeit verbindet ein formales Modell von Datennetzen und Data Products mit einer wirtschaftlichen Betrachtung von Fehlerbudgets, einer Fallstudie zur Margenanalyse und einem schrittweisen Vorgehen für Organisationen. KI wird dabei zunächst als Hinweis- und Gegenprüfungswerkzeug verstanden. Abweichungen zwischen KI-Antwort und Unternehmensanalyse können auf Datenlücken hinweisen, aber auch eine unvollständige interne Analyse sichtbar machen.

> **Leitgedanke:** Nicht nur fragen, ob die KI gut genug ist, sondern ob das Datennetz für diese konkrete Frage gut genug ist.

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Kernaussagen](#kernaussagen)
- [Inhalt der Arbeit](#inhalt-der-arbeit)
- [Fallstudie: sinkende Marge](#fallstudie-sinkende-marge)
- [Formales Modell und wirtschaftliche Perspektive](#formales-modell-und-wirtschaftliche-perspektive)
- [Vertrauensstufen](#vertrauensstufen)
- [Data Products und Verantwortlichkeiten](#data-products-und-verantwortlichkeiten)
- [Projektstruktur](#projektstruktur)
- [Voraussetzungen](#voraussetzungen)
- [PDF erstellen](#pdf-erstellen)
- [Prüfen und weiterentwickeln](#prüfen-und-weiterentwickeln)
- [Stand und Grenzen](#stand-und-grenzen)
- [Quellen und weiterführende Arbeiten](#quellen-und-weiterführende-arbeiten)
- [Software und Tests](#software-und-tests)
- [Lizenz und Nutzung](#lizenz-und-nutzung)

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

## Fallstudie: sinkende Marge

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

## Projektstruktur

```text
aidataeco/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
├── tests/
├── examples/
└── science/
    ├── aidataeco.tex
    ├── aidataeco.pdf
    └── aidataeco.synctex.gz
```

Im Arbeitsverzeichnis können zusätzlich lokale LaTeX-Hilfsdateien wie `.aux`, `.log`, `.toc`, `.out`, `.fls` und `.fdb_latexmk` entstehen. Sie sind Build-Artefakte und keine eigenständigen Quellen der Arbeit.

| Datei | Zweck |
|---|---|
| [`science/aidataeco.tex`](science/aidataeco.tex) | Maßgebliche editierbare Quelle der deutschen Arbeit. |
| [`science/aidataeco.pdf`](science/aidataeco.pdf) | Daraus erzeugte Lesefassung; nach Änderungen an der TeX-Quelle neu bauen. |
| [`science/aidataeco.synctex.gz`](science/aidataeco.synctex.gz) | SyncTeX-Zuordnung zwischen PDF und TeX-Quelle für unterstützte Editoren. |
| [`src/`](src) | Python-Bausteine zur Arbeit (siehe [Software und Tests](#software-und-tests)). |
| [`tests/`](tests) | Automatisierte Tests mit `pytest`. |
| [`examples/`](examples) | Beispiel-Spezifikation und Beispiel-Antworten zur Fallstudie für das Prüfwerkzeug. |
| [`pyproject.toml`](pyproject.toml) | Paket-, Abhängigkeits-, pytest- und Coverage-Konfiguration. |
| [`LICENSE`](LICENSE) | Nutzungsbedingungen für die Inhalte dieses Repositories. |
| [`.gitignore`](.gitignore) | Ignorierte lokale Umgebungs- und Build-Dateien. |

Die englische Konzeptdatei, auf der die inhaltliche Ausarbeitung beruht, ist **nicht** Teil dieses Repositorys. Die Arbeit und dieses Repository enthalten daher keine automatisch synchronisierte Übersetzung.

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

### Prüfwerkzeug: Freigabebericht und Monitoring

Das Werkzeug setzt den Abschnitt „Operationalisierung" der Arbeit um. Eine Spezifikation (JSON oder YAML, Beispiel: [`examples/sales_result_360.yaml`](examples/sales_result_360.yaml)) beschreibt Datennetz, Data Product, Verantwortliche und den Anwendungsfall mit Stufe, Error Budget und Referenzfragen. Kennzahlen, Provenance, Qualität und Error Budget werden aus den Daten **abgeleitet**; in der Spezifikation erklärt werden nur die organisatorischen Nachweise (Mensch entscheidet, Freigabe, Protokollierung, Eingriffspfad).

```bash
# Bericht erstellen (Markdown auf der Standardausgabe; --format json für den Archivstand)
python -m aidataeco report examples/sales_result_360.yaml \
    --answers examples/answers_sales_result_360.json --today 2026-10-22 --expected-loss 380

# Zwei gespeicherte Berichte vergleichen (Monitoring über die Zeit)
python -m aidataeco report SPEC --answers ANTWORTEN --format json --output bericht-2026-10.json
python -m aidataeco compare bericht-2026-09.json bericht-2026-10.json
```

Ohne `--answers` gilt jede Referenzfrage als unbeantwortet. Exit-Codes: `0` kein Freigabehindernis bzw. keine Regression, `1` Freigabehindernis bzw. Regression, `2` ungültige Eingabe. Damit lässt sich der Bericht in eine Pipeline einbinden. Der Fingerprint eines Berichts bindet Spezifikation, Antworten, Stichtag, erwarteten Verlust und Versionen; das Ergebnis geht nicht ein.

Die KI-Anwendung wird über eine Funktion `Frage -> Answer` angebunden (`provider.AnswerProvider`); ein Adapter, der keine Antwort liefern kann, löst `ProviderError` aus, das zählt als unbeantwortet. Konkrete Adapter (etwa MCP) und eine Web-Schicht (FastAPI) sind bewusst nicht Teil des Kerns. YAML benötigt PyYAML (`pip install -e ".[yaml]"`, in `.[dev]` enthalten); JSON funktioniert ohne Zusatzpaket.

Der Bericht ist keine Freigabe. Er weist Hindernisse aus; die Entscheidung trifft der Use-Case Owner. Der Vergleich ist exakt und ohne Toleranz und ist nur sinnvoll, wenn die Referenzfragen gleich geblieben sind (siehe Arbeit, Abschnitt „Vergleich über die Zeit").

### Wiederverwendung von subgraph-sat-solver-econ

Entscheider, Schaltkreisbausteine und die Formel der Rechenlücke werden nicht neu geschrieben, sondern aus [`subgraph-sat-solver-econ`](https://github.com/naphz86/subgraph-sat-solver-econ) importiert (`subgraph_sat_solver_econ`): `integration` formuliert nur das Problem und nutzt `Problem`, `maximize` und `DpllBackend`; `evaluation` berechnet den erklärten Anteil mit `computation_gap` und `total_output`. Die Abhängigkeit steht in `pyproject.toml`. Damit das Referenzprojekt unter diesem Namen importierbar ist, braucht es dort die Paketabbildung `package-dir = { subgraph_sat_solver_econ = "src" }` (siehe dessen `pyproject.toml`).

### Installieren und testen

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

`pytest` führt alle Tests aus und erzeugt den Coverage-Bericht (Zeilen und Zweige) als HTML unter `doc/coverage/index.html`. Der Bericht ist ein Build-Artefakt und wird bei Bedarf neu erzeugt.

## Lizenz und Nutzung

Die Datei [`LICENSE`](LICENSE) enthält spezifische, restriktive Nutzungsbedingungen und ist **keine übliche Open-Source-Lizenz**. Vor Kopieren, Weiterverbreiten, Verändern oder einer kommerziellen Nutzung sind die Lizenzbedingungen zu lesen und zu klären. Die hier beschriebene Lizenz darf nicht als pauschale Erlaubnis zur Nutzung wissenschaftlicher Inhalte oder zur Generierung daraus abgeleiteter Software ausgelegt werden.

Für Fragen zur wissenschaftlichen Einordnung oder zu gewünschten zukünftigen Softwarebestandteilen ist eine konkrete Beschreibung des Anwendungsfalls, der Eingaben, der erwarteten Ausgaben und des gewünschten Prüfverhaltens die beste Grundlage für die weitere Umsetzung.
