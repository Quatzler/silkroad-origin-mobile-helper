# Phase 5: Erster Test-Hotkey

In dieser Phase wurde das Input-System und die Mapping-Engine implementiert, um globale Hotkeys zu unterstützen, die nur aktiv sind, wenn das Ziel-Fenster fokussiert ist.

## Ziel

Implementierung eines Hotkeys (F8), der eine Log-Ausgabe erzeugt, wenn Silkroad Origin Mobile fokussiert ist.

## Architektur

Die Implementierung folgt der Clean Architecture:

1.  **Domain (`src/silkroad_companion/domain/input_service.py`)**: Abstraktes Interface `InputService` für Tastatureingaben.
2.  **Infrastructure (`src/silkroad_companion/infrastructure/keyboard_input_service.py`)**: Implementierung des Interfaces mittels der `keyboard` Python-Bibliothek.
3.  **Application (`src/silkroad_companion/application/mapping_engine.py`)**: Die Mapping-Engine verknüpft die Konfiguration (YAML) mit dem Input-Service. Sie sorgt dafür, dass:
    *   Hotkeys nur registriert werden, wenn die Engine aktiviert ist.
    *   Mappings basierend auf dem aktuellen Spielzustand (`GAME`, `INVENTORY`, etc.) gewechselt werden können.
4.  **Presentation (`src/silkroad_companion/presentation/main_window.py`)**: Das Hauptfenster steuert die Aktivierung der Mapping-Engine basierend auf dem Fensterfokus.

## Sicherheit & Fokus-Handling

Um unerwünschte Eingaben in anderen Anwendungen zu verhindern:
*   Die Mapping-Engine wird automatisch deaktiviert (`unbind_all`), sobald Waydroid den Fokus verliert.
*   Beim Wiedererlangen des Fokus werden die Mappings für den aktuellen Zustand neu geladen.

## Testergebnisse

*   **Unit Tests**: 11/11 Tests erfolgreich bestanden (inklusive neuer Tests für die Mapping-Engine).
*   **Manuelle Prüfung**: In der Konfiguration wurde `F8` auf die Action `test_log` gemappt. Wenn das Fenster fokussiert ist, führt das Drücken von F8 zu einer Konsolenausgabe.

## Risiken

*   **Root-Rechte**: Die `keyboard`-Bibliothek benötigt unter Linux Zugriff auf `/dev/input/`. Falls die Anwendung nicht als Root oder mit entsprechenden Gruppenrechten gestartet wird, kann die Hotkey-Registrierung fehlschlagen. Alternativ müssten spezialisierte Wayland-Protokolle genutzt werden, die jedoch oft Desktop-spezifisch sind.
