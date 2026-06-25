# Phase 3: Window Tracking

In dieser Phase wurde die Fähigkeit implementiert, die Position und Größe des Silkroad-Fensters in Echtzeit zu verfolgen.

## Ziel

Das Tool muss jederzeit wissen, wo sich das Silkroad-Fenster befindet, um Klicks und UI-Erkennung relativ zum Fenster durchführen zu können. Absolute Monitor-Koordinaten sind verboten.

## Implementierung

Die Implementierung baut auf dem KWin-Scripting-Ansatz aus Phase 2 auf:

1.  **Erweitertes KWin-Script**: Das JavaScript in KWin wurde so erweitert, dass es bei jedem Fokuswechsel (oder initial) die Geometrie (`x`, `y`, `width`, `height`) des Fensters über `console.log` an das System-Journal sendet.
2.  **WindowService (Domain)**: Ein neues Interface definiert den Zugriff auf Fenster-Informationen.
3.  **KWinFocusService (Infrastructure)**: Implementiert nun auch `WindowService`. Der Journal-Monitor parst zusätzlich die `SRO_GEOMETRY`-Zeilen.
4.  **WindowTracker (Application)**: Ein dedizierter Use-Case überwacht Änderungen der Geometrie und benachrichtigt registrierte Beobachter (wie die GUI).
5.  **MainWindow (Presentation)**: Zeigt die aktuellen Koordinaten und die Größe des Fensters an.

## Vorteile

*   **Relative Koordinaten**: Alle zukünftigen Aktionen (Klicks, Vision) können nun basierend auf diesen Daten berechnet werden.
*   **Performance**: Das Tracking erfolgt ereignisbasiert über KWin, was Ressourcen schont.
*   **Wayland-kompatibel**: Umgeht die Sicherheitsbeschränkungen von Wayland bezüglich globaler Fensterabfragen durch die Nutzung des KWin-internen Scriptings.

## Risiken

*   **Skalierung/DPI**: Aktuell wird von einem Skalierungsfaktor von 1.0 ausgegangen. Bei High-DPI-Monitoren müssen die Koordinaten eventuell noch mit dem Screen-Scaling verrechnet werden. Dies ist für eine spätere Phase (DPI-Handling) vorgesehen.

## Fehlerbehebungen & Stabilität

Während der Testphase wurden folgende Probleme behoben:
- **Robustes Parsing**: Die Anwendung verarbeitet nun korrekt Journal-Einträge mit Präfixen (z.B. `js: `).
- **Float-Koordinaten**: KWin liefert bei aktiver Desktop-Skalierung teilweise Fließkommazahlen für die Geometrie. Diese werden nun robust geparst und in Ganzzahlen umgewandelt.

## Testergebnisse

*   **Unit Tests**: Erfolgreich (7/7 passed, inklusive neuem `test_parsing.py`).
*   **Integration**: Die Kommunikation zwischen KWin -> Journal -> Python funktioniert stabil auch bei verschiedenen Skalierungseinstellungen.
*   **Manuelle Verifizierung**: Die GUI aktualisiert sich korrekt und ohne Fehlermeldungen bei Fensterbewegungen.
