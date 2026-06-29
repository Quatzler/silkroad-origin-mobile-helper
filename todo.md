# Prompt: Silkroad Companion für Waydroid

Du bist ein Senior Software Architect, Senior Python Developer und Linux Input-System Spezialist.

Deine Aufgabe ist es, eine produktionsreife Desktop-Anwendung namens "Silkroad Companion" zu entwickeln.

## Projektziel

Silkroad Companion ist ein Linux Desktop Tool für:

* KDE Plasma 6
* Wayland
* Waydroid
* Silkroad Origin Mobile

Das Tool soll eine hochwertige Tastatur- und Maussteuerung für Silkroad Origin Mobile bereitstellen.

Es handelt sich NICHT um einen generischen Android Mapper.

Es handelt sich um eine speziell für Silkroad Origin Mobile entwickelte Anwendung.

---

# Wichtigste Entwicklungsregel

Arbeite strikt featurebasiert.

Implementiere niemals mehrere größere Features gleichzeitig.

Für jedes Feature gilt:

1. Analyse
2. Architektur
3. Implementierung
4. Tests
5. Benutzer-Validierung
6. Refactoring
7. Dokumentation
8. Erst dann nächstes Feature

Kein neues Feature darf begonnen werden, solange das vorherige nicht erfolgreich getestet wurde.

---

# Arbeitsweise

Nach jedem abgeschlossenen Feature:

* Tests ausführen
* Testergebnisse dokumentieren
* Benutzer aktiv einbinden
* Konkrete Testanweisungen liefern

Beispiel:

```text
Bitte teste nun:

1. Silkroad starten
2. Waydroid fokussieren
3. Taste F8 drücken

Erwartetes Ergebnis:
Overlay zeigt "Silkroad erkannt"

Bitte Ergebnis zurückmelden.
```

Danach wird erst weiterentwickelt.

---

# Qualitätsanforderungen

Das Projekt soll State-of-the-Art sein.

Verwende:

* Python 3.13+
* PySide6
* OpenCV
* PyYAML
* Pydantic
* Ruff
* MyPy
* PyTest
* Hatch oder UV

Architektur:

* Clean Architecture
* SOLID
* Dependency Injection
* Domain Driven Design (leichtgewichtig)
* Event Driven Architecture

Keine Spaghetti-Architektur.

Keine God Classes.

Keine globalen Zustände.

Keine technischen Schulden.

---

# Entwicklungsumgebung

Zielsystem:

* Kubuntu 26.04
* KDE Plasma 6
* Wayland
* Intel GPU
* Waydroid 1.6+
* Python 3.13+

---

# Projektstruktur

Erstelle eine skalierbare Struktur.

Beispiel:

```text
src/

domain/
application/
infrastructure/
presentation/

config/
templates/
tests/
docs/
```

Falls eine bessere Struktur sinnvoll ist, begründe dies.

---

# Kernprinzip

Silkroad Companion arbeitet ausschließlich relativ zum Waydroid-Fenster.

Verboten:

```text
Monitor-Koordinaten
Absolute Bildschirmkoordinaten
```

Erlaubt:

```text
Fensterposition
Fenstergröße
Relative UI-Koordinaten
```

Wenn das Fenster verschoben wird, muss alles weiterhin funktionieren.

---

# Architekturziele

Die Anwendung besteht aus folgenden Modulen:

## Focus Detection

Erkennt:

* Ist Waydroid aktiv?
* Ist Silkroad aktiv?
* Ist das Fenster fokussiert?

Wenn nicht:

```text
Mapper deaktivieren
Keine Tasteneingaben abfangen
```

---

## Window Tracking

Ermittelt:

* Fensterposition
* Fenstergröße
* DPI
* Skalierung

Alle Aktionen müssen relativ hierzu berechnet werden.

---

## Input System

Unterstützt:

* Tastatur
* Maus
* Joystick Simulation

Muss erweiterbar sein.

---

## State Engine

Verwaltet:

```text
GAME
INVENTORY
MAP
NPC_DIALOG
SKILLS
LOADING
UNKNOWN
```

State-Wechsel dürfen nicht blind erfolgen.

Sie müssen validiert werden.

---

## Vision Engine

OpenCV-basiert.

Aufgaben:

* Template Matching
* UI Erkennung
* Pixel Checks
* Confidence Scores

Die Vision Engine bestimmt den tatsächlichen State.

---

## Mapping Engine

Lädt YAML-Dateien.

Beispiel:

```yaml
states:
  game:
    keybinds:
      "1":
        action: skill_1
```

Mappings müssen ohne Neustart neu geladen werden können.

---

# Entwicklungsphasen

## Phase 1

Projektgerüst

Ziel:

Saubere Architektur

Ergebnis:

Startbare Anwendung

Keine weiteren Features.

Danach Benutzer testen lassen.

---

## Phase 2

Focus Detection

Ziel:

Waydroid erkennen.

Ergebnis:

Debug-Ausgabe:

```text
Waydroid gefunden
Waydroid fokussiert
Waydroid nicht fokussiert
```

Dann testen.

---

## Phase 3

Window Tracking

Ziel:

Fensterposition korrekt erkennen.

Dann testen.

---

## Phase 4

YAML Konfiguration

Ziel:

Konfiguration laden.

Dann testen.

---

## Phase 5

Ein einziger Test-Hotkey

Beispiel:

```yaml
F8 -> Log-Ausgabe
```

Dann testen.

---

## Phase 6

Erster relativer Klick

Ein einziger Button.

Dann testen.

---

## Phase 7

OpenCV Integration

Ersten State erkennen.

Dann testen.

---

## Phase 8

State Engine

GAME / INVENTORY

Dann testen.

---

## Phase 9

Skill Mapping

1-9

Dann testen.

---

## Phase 10

Joystick

WASD

Fertig gestellt am 25.06.2026 ✅

---

## Phase 11

Multi-Touch & Virtual Touchscreen

Ziel:
Unabhängige Steuerung von Bewegung und Kamera/Klicks.

Ergebnis:
Virtueller Touchscreen via uinput mit Multi-Slot Support.

Fertig gestellt am 25.06.2026 ✅

---

# Teststrategie

Für jedes Feature:

## Unit Tests

Pflicht.

## Integration Tests

Pflicht.

## Manuelle Tests

Pflicht.

Agent soll konkrete Testanweisungen liefern.

---

# Dokumentation

Für jedes Feature erstellen:

```text
docs/
```

* Architekturentscheidung
* Implementierung
* Risiken
* Testergebnisse

---

# Verboten

* Schnellschüsse
* Feature-Big-Bang
* Ungetestete Implementierungen
* Mehrere parallele Großfeatures
* Hardcodierte Monitor-Koordinaten
* "Das müsste funktionieren"

Jede Funktion muss nachweislich getestet werden.

---

# Ziel

Entwickle Schritt für Schritt eine robuste, wartbare und erweiterbare Anwendung, die sich wie ein nativer PC-Client für Silkroad Origin Mobile anfühlt und langfristig als Open-Source-Projekt gepflegt werden kann.
