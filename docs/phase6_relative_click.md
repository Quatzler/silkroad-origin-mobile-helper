# Phase 6: Erster relativer Klick

In dieser Phase wurde die Fähigkeit implementiert, Mausklicks relativ zum Silkroad-Fenster auszuführen.

## Ziel

Implementierung eines relativen Klicks, der durch den Hotkey F8 ausgelöst wird und genau in die Mitte des Silkroad-Fensters zielt, unabhängig von dessen Position auf dem Bildschirm.

## Architektur

Die Implementierung erweitert das Input-System:

1.  **Domain (`src/silkroad_companion/domain/input_service.py`)**: Neues Interface `MouseService` mit Methoden für relative Klicks und Mausbewegungen.
2.  **Infrastructure (`src/silkroad_companion/infrastructure/mouse_input_service.py`)**: Implementierung mittels `pynput.mouse`. Die Koordinaten werden basierend auf der aktuellen `WindowInfo` (x, y, w, h) berechnet.
3.  **Application (`src/silkroad_companion/application/mapping_engine.py`)**: Die Mapping-Engine nutzt nun sowohl `InputService` (Tastatur) als auch `MouseService` (Maus). Bei der Action `test_click` wird der `WindowTracker` abgefragt, um die aktuellen Fensterkoordinaten für den Klick zu erhalten.

## Technische Details

*   **Relative Koordinaten**: Klicks werden in Werten von 0.0 bis 1.0 angegeben (z.B. 0.5, 0.5 für die Mitte).
*   **Bibliotheks-Wechsel**: Um die Stabilität zu erhöhen und die Abhängigkeit von Root-Rechten zu minimieren, wurde von `keyboard` auf `pynput` gewechselt. `pynput` bietet eine einheitliche API für Tastatur- und Maussteuerung.

## Testergebnisse

*   **Unit Tests**: 11/11 Tests erfolgreich bestanden.
*   **Integration**: Die `MappingEngine` verknüpft nun erfolgreich Hotkeys mit Maus-Aktionen.

## Risiken

*   **Wayland Security**: Unter Wayland können globale Klicks eingeschränkt sein. `pynput` versucht dies über Standard-Schnittstellen zu lösen, erfordert aber oft, dass die Anwendung Zugriff auf die Input-Devices hat (Gruppe `input`).
*   **Skalierung**: Bei High-DPI Displays müssen die Koordinaten eventuell noch angepasst werden (wird in zukünftigen Phasen verfeinert).
