# Phase 11: Joystick Optimierung & Hot Reload

In dieser Phase wurden zwei wesentliche Komfort- und Steuerungs-Features implementiert:

1. **Hot Reload der Konfiguration**: Die Anwendung überwacht nun die `settings.yaml`. Änderungen an Keybindings, Koordinaten oder Joystick-Einstellungen werden sofort übernommen, ohne dass die Anwendung neu gestartet werden muss.
2. **Verbesserte Joystick-Steuerung**:
    * **Swipe-Simulation**: Beim ersten Tastendruck eines Richtungskeys wird ein "Swipe" vom Joystick-Zentrum zur Zielposition simuliert. Dies ist für viele Mobile-Spiele (wie Silkroad) notwendig, um die Bewegung zu registrieren.
    * **Multi-Direction Support**: Es können nun mehrere Tasten gleichzeitig gedrückt werden (z.B. W+D für diagonales Laufen). Die Mapping Engine berechnet dynamisch den resultierenden Richtungsvektor.
    * **Konfigurierbarkeit**: Joystick-Zentrum und Radius können nun pro State in der `settings.yaml` definiert werden.

## Technische Details

### Joystick-Logik (`MappingEngine`)
Die Engine hält nun einen internen Zustand der aktiven Richtungen (`_active_directions`).
Bei jeder Änderung wird der Vektor neu berechnet:
- Wenn diagonal: Der Vektor wird normalisiert, damit die Auslenkung des Joysticks konstant bleibt.
- Start-Logik: Falls noch kein Key aktiv war, wird `press_relative` (Center) -> `move_relative` (Target) ausgeführt.
- Update-Logik: Falls bereits Keys aktiv sind, wird nur `move_relative` zum neuen Target ausgeführt.
- Stop-Logik: Wenn alle Keys losgelassen werden, erfolgt ein `release_relative`.

### Hot Reload (`MainWindow`)
Ein `QFileSystemWatcher` beobachtet die Datei `config/settings.yaml`.
Beim Signal `fileChanged` wird:
1. Die Konfiguration via `ConfigLoader` neu geladen.
2. Das `AppConfig`-Objekt in der `MappingEngine` ausgetauscht.
3. Falls die Engine aktiv ist, werden alle Hotkeys entbunden und mit der neuen Konfiguration neu registriert.

## Benutzung
Ändere einfach Werte in der `config/settings.yaml` und speichere die Datei. In der Konsole erscheint die Meldung:
`Hot Reload: Konfiguration erfolgreich neu geladen.`
