# Phase 13: Virtual Touchscreen & Multi-Touch

In dieser Phase wurde die Eingabesteuerung von einer einfachen Maus-Simulation auf einen virtuellen Multi-Touchscreen umgestellt. Dies ermöglicht die gleichzeitige Steuerung von Bewegung (Joystick) und anderen Aktionen (Klicks/Skills), ohne dass sich diese gegenseitig blockieren.

## Änderungen

1.  **Touchscreen-Emulation**:
    *   Anstatt einer virtuellen Maus wird nun ein virtueller Touchscreen (`EvdevTouchService`) via `uinput` erstellt.
    *   Das Gerät unterstützt das Linux Multi-Touch-Protokoll (Type B).
2.  **Multi-Touch Slots**:
    *   Die `MappingEngine` nutzt nun verschiedene "Slots" für gleichzeitige Eingaben.
    *   **Slot 0**: Reserviert für Klicks, Skills und allgemeine UI-Interaktionen.
    *   **Slot 1**: Reserviert für den virtuellen Joystick (WASD).
3.  **Unabhängigkeit von der physischen Maus**:
    *   Da die Eingaben nun als Touch-Events gesendet werden, bleibt der physische Mauszeiger des Systems unbeeinflusst.
    *   Dies erlaubt es, gleichzeitig mit WASD zu laufen und mit der echten Maus die Kamera im Spiel zu drehen.
4.  **Infrastruktur**:
    *   `TouchService`-Interface in der Domain definiert.
    *   `EvdevTouchService` implementiert die Low-Level `uinput`-Kommunikation.

## Verifizierung

*   **Automatisierte Tests**: 25 Tests (inkl. Multi-Touch Slot-Logik) erfolgreich bestanden.
*   **Architektur**: Saubere Trennung der Input-Services nach Clean Architecture Prinzipien.

## Fehlerbehebungen & Optimierungen

Während der Implementierung wurden folgende kritische Punkte adressiert:

1.  **Koordinaten-Skalierung**:
    *   Die relativen Koordinaten (0.0 bis 1.0) werden nun präzise auf den gesamten Desktop-Bereich gemappt, indem die Bildschirmauflösung aller Monitore beim Start ermittelt wird.
2.  **Focus-Loss Reset**:
    *   Beim Wechsel des Fensters (Fokusverlust) führt der Dienst nun einen automatischen Reset durch. Alle aktiven Touch-Punkte werden losgelassen, um "hängengebliebene" Eingaben zu vermeiden, die das System blockieren könnten.
3.  **Protokoll-Kompatibilität**:
    *   Das Gerät sendet nun zusätzlich Single-Touch Events (`ABS_X`, `ABS_Y`), um eine bessere Kompatibilität mit Wayland-Compositoren und Waydroid zu gewährleisten.

## Testanweisungen

1.  Starte die Anwendung: `uv run python main.py`
2.  Fokussiere das Silkroad-Fenster.
3.  Halte **W** gedrückt, um zu laufen.
4.  Bewege währenddessen deine physische Maus, um die Kamera zu drehen.
5.  Drücke eine Skill-Taste (z.B. **1**), während du weiterhin läufst.

**Erwartetes Ergebnis**:
*   Dein Charakter läuft kontinuierlich weiter, auch wenn du die Kamera drehst oder Skills aktivierst.
*   Der physische Mauszeiger springt nicht mehr wild über den Bildschirm.
