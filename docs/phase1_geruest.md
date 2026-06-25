# Phase 1: Projektgerüst

## Architekturentscheidung

Das Projekt folgt der **Clean Architecture** mit einer klaren Trennung von Belangen:

*   **Domain**: Enthält die Geschäftslogik, Modelle und Schnittstellen. Frei von externen Abhängigkeiten (außer Pydantic für Datenvalidierung).
*   **Application**: Enthält Use Cases und Services, die die Domänenlogik koordinieren.
*   **Infrastructure**: Enthält Implementierungen für externe Systeme (Wayland Tracking, OpenCV, Input System).
*   **Presentation**: Enthält die Benutzeroberfläche (PySide6).

Die Paketverwaltung erfolgt über `uv`, was eine schnelle und reproduzierbare Umgebung garantiert.

## Implementierung

*   `pyproject.toml` mit Konfiguration für Ruff (Linting), MyPy (Typ-Prüfung) und PyTest.
*   Basis-Verzeichnisstruktur erstellt.
*   Minimaler PySide6-Einstiegspunkt in `src/silkroad_companion/main.py`.
*   Domänenmodelle (`AppState`, `WindowInfo`) in `src/silkroad_companion/domain/models.py`.

## Risiken

*   **GUI-Abhängigkeiten**: PySide6 benötigt zur Laufzeit ein funktionierendes Display-System (Wayland/X11). In CI-Umgebungen muss der `offscreen` Modus verwendet werden.
*   **Python 3.14**: Da Python 3.14 verwendet wird (neueste Version), könnten einige Bibliotheken noch experimentell reagieren, bisher gab es aber keine Probleme.

## Testergebnisse

*   Unit Tests für Domänen-Enums erfolgreich.
*   Integrationstest für MainWindow (Offscreen) erfolgreich.
*   Ruff & MyPy ohne Beanstandungen.
