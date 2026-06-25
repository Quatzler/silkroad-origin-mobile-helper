# Phase 8: State Engine (GAME / INVENTORY)

## Ziel
Implementierung einer intelligenten Zustandserkennung basierend auf Template-Matching, um zwischen verschiedenen Spielszenarien (Login, Game, Inventory) zu unterscheiden und die Steuerung dynamisch anzupassen.

## Architekturentscheidungen
- **Template-Matching**: Nutzung von OpenCV `matchTemplate` (CCOEFF_NORMED) zur Identifizierung markanter UI-Elemente.
- **Hierarchische Erkennung**: Priorisierung von spezifischen Zuständen (Inventory, Login) vor dem allgemeinen Spielzustand (Game).
- **Entkopplung**: Die `VisionEngine` meldet Zustandsänderungen via Observer-Pattern an die `MappingEngine`.

## Implementierung
- **VisionEngine**: Lädt beim Start alle Templates aus dem Verzeichnis `templates/`.
- **MappingEngine**: Unterstützt nun kontextabhängige Aktionen. Im `inventory`-State löst die `ESC`-Taste einen relativen Klick auf den Zurück-Button aus.
- **Konfiguration**: `settings.yaml` wurde um den `inventory`-State erweitert.
- **Wayland-Capture**: Da `QScreen.grabWindow` unter Wayland (KDE Plasma 6) oft leere Bilder liefert, wurde ein Fallback via `spectacle` implementiert. Dies ermöglicht die Zustandserkennung im Hintergrund (ca. alle 1-2 Sekunden).

## Risiken
- **Skalierung**: Template-Matching ist empfindlich gegenüber Änderungen der Fenstergröße. Wenn Waydroid mit einer anderen Auflösung als die Referenz-Screenshots läuft, schlägt die Erkennung fehl.
- **Performance**: Das Aufrufen von `spectacle` für jeden Frame-Check erzeugt eine gewisse CPU-Last. Die Frequenz wurde daher auf 1 Hz optimiert.

## Testergebnisse
- **Unit Tests**: 4 Tests in `test_vision.py` und 4 Tests in `test_mapping.py` erfolgreich bestanden.
- **Template Extraktion**: Templates wurden erfolgreich aus den Benutzer-Screenshots extrahiert.
