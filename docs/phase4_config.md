# Phase 4: YAML Konfiguration

In dieser Phase wurde das Konfigurationssystem implementiert, welches es ermöglicht, Tastenbelegungen und Anwendungseinstellungen über eine externe YAML-Datei zu steuern.

## Ziel

Die Anwendung soll ohne Code-Änderungen anpassbar sein. Mappings für verschiedene Spielzustände (States) werden in einer zentralen Konfigurationsdatei definiert.

## Implementierung

1.  **Domain-Modelle (`src/silkroad_companion/domain/config.py`)**: Nutzung von Pydantic zur Definition einer typsicheren Konfigurationsstruktur (`AppConfig`, `StateConfig`, `KeyBind`).
2.  **Config-Loader (`src/silkroad_companion/infrastructure/config_loader.py`)**: Eine Komponente, die YAML-Dateien lädt und gegen die Domain-Modelle validiert. Falls keine Datei vorhanden ist, werden sinnvolle Standardwerte verwendet.
3.  **Beispiel-Konfiguration (`config/settings.yaml`)**: Eine erste Vorlage mit Beispiel-Keybinds für den `game` und `inventory` State.
4.  **GUI-Integration**: Das Hauptfenster zeigt nun an, wie viele States aus der Konfiguration geladen wurden.

## Vorteile

*   **Flexibilität**: Benutzer können eigene Mappings erstellen, ohne die Anwendung neu kompilieren zu müssen.
*   **Validierung**: Dank Pydantic werden Fehler in der YAML-Datei (z.B. falsche Datentypen) sofort beim Start erkannt.
*   **Wartbarkeit**: Klare Trennung zwischen Konfigurationsstruktur und Logik.

## Testergebnisse

*   **Unit Tests**: Erfolgreich (9/9 passed, inklusive `test_config.py`).
*   **Manuelle Verifizierung**: Die Anwendung startet korrekt, lädt die `config/settings.yaml` und zeigt den Status in der GUI an.
