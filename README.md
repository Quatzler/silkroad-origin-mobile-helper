# Silkroad Companion

Silkroad Companion ist ein spezialisiertes Linux-Desktop-Tool zur Steuerung von Silkroad Origin Mobile auf Waydroid unter KDE Plasma 6.

## Features

✅ **Focus Detection** - Erkennt automatisch, wann Silkroad Origin Mobile fokussiert ist
✅ **Window Tracking** - Verfolgt Fensterposition und -größe für präzise Koordinaten
✅ **Vision System** - Zustandserkennung via OpenCV Template Matching
✅ **Mapping Engine** - YAML-basierte Tastatur-zu-Touch-Mapping
✅ **State Engine** - Dynamische Keymaps basierend auf Spielzustand
✅ **Touch Calibration** - Kalibrierungssystem für präzise Touch-Positionen
✅ **Multi-Slot Touch** - Gleichzeitige Touch-Events für Joystick und Klicks

## Entwicklung

Dieses Projekt verwendet `uv` für das Paketmanagement.

### Voraussetzungen

* Python 3.13+
* KDE Plasma 6 (Wayland)
* Waydroid
* Berechtigungen für `/dev/input/` und `/dev/uinput`

### Setup

```bash
uv sync
```

### Starten

```bash
uv run python main.py
```

#### Linux Berechtigungen (Hotkeys & Klicks)

Damit die globalen Hotkeys und Klicks funktionieren, benötigt die Anwendung unter Linux Zugriff auf `/dev/input/` und `/dev/uinput`.

**Option A (Empfohlen): udev Rule**
Erstelle eine Datei `/etc/udev/rules.d/99-silkroad.rules`:
```text
KERNEL=="uinput", GROUP="input", MODE="0660"
KERNEL=="event*", GROUP="input", MODE="0660"
```
Füge deinen User der Gruppe `input` hinzu:
```bash
sudo usermod -aG input $USER
```
Danach musst du den Computer neu starten, damit die Gruppenänderung für deine gesamte Desktop-Session (inkl. Wayland) übernommen wird.

**Option B (Schnell): Mit sudo**
Wenn du `sudo` verwenden musst, stelle sicher, dass die Umgebung korrekt übergeben wird:
```bash
sudo env "PATH=$PATH" uv run python main.py
```

## Touch-Kalibrierung

**WICHTIG:** Bevor du die Anwendung nutzt, musst du die Touch-Kalibrierung durchführen!

### Automatische Kalibrierung (Empfohlen)

```bash
uv run python calibrate_touch.py
```

Folge den Anweisungen im Kalibrierungs-Tool, um die optimalen Parameter zu finden.

### Manuelle Kalibrierung

1. Starte das Debug-Tool:
```bash
uv run python debug_window.py
```

2. Notiere die Fenstergeometrie und teste verschiedene Positionen
3. Passe die Parameter in `config/settings.yaml` an:

```yaml
touch_calibration:
  scale_x: 1.0    # Skalierungsfaktor X-Achse
  scale_y: 1.0    # Skalierungsfaktor Y-Achse
  offset_x: 0     # Pixel-Offset X-Achse
  offset_y: 0     # Pixel-Offset Y-Achse
```

### Dokumentation

Ausführliche Anleitung: [docs/TOUCH_CALIBRATION.md](docs/TOUCH_CALIBRATION.md)

## Konfiguration

Die Anwendung wird über YAML-Dateien konfiguriert. Siehe `config/settings.yaml` für ein Beispiel.

### States

Die Anwendung unterstützt verschiedene Spielzustände (States) mit unterschiedlichen Keymaps:

```yaml
states:
  game:        # Spielwelt
    keybinds:
      W: { action: "move_forward" }
      A: { action: "move_left" }
      S: { action: "move_backward" }
      D: { action: "move_right" }
      "1": { action: "skill_1", x: 0.7, y: 0.9 }
      "2": { action: "skill_2", x: 0.75, y: 0.9 }
  
  menu:        # Menü
    keybinds:
      ESC: { action: "back_button_click", x: 0.05, y: 0.05 }
  
  inventory:   # Inventar
    keybinds:
      ESC: { action: "back_button_click", x: 0.05, y: 0.05 }
```

### Joystick-Konfiguration

Der virtuelle Joystick kann konfiguriert werden:

```yaml
states:
  game:
    joystick:
      center_x: 0.15    # X-Position der Joystick-Mitte (relativ)
      center_y: 0.75    # Y-Position der Joystick-Mitte (relativ)
      radius: 0.05      # Maximale Auslenkung
    keybinds:
      W: { action: "move_forward" }
      A: { action: "move_left" }
      S: { action: "move_backward" }
      D: { action: "move_right" }
```

## Gleichzeitige Maus- und Touch-Steuerung

Die Anwendung unterstützt **gleichzeitiges Laufen (WASD) und Kamera-Drehen (Maus)**:

- **Maus**: Bleibt System-Maus für Kamera-Steuerung
- **WASD**: Wird zu Touch-Joystick (Slot 1) für Bewegung
- **Skills 1-9**: Wird zu Touch-Klicks (Slot 0) für Fähigkeiten

Die verschiedenen Touch-Typen nutzen **separate Slots**, damit sie sich nicht gegenseitig beeinflussen.

## Tests ausführen

```bash
uv run pytest
```

## Linting & Typ-Check

```bash
uv run ruff check .
uv run mypy src
```

## Projektstruktur

```
silkroad-companion/
├── src/
│   └── silkroad_companion/
│       ├── application/       # Anwendungslogik
│       │   ├── focus_tracker.py
│       │   ├── mapping_engine.py
│       │   ├── vision_engine.py
│       │   └── window_tracker.py
│       ├── domain/             # Domänenmodelle
│       │   ├── config.py
│       │   ├── focus_service.py
│       │   ├── input_service.py
│       │   ├── models.py
│       │   ├── vision_service.py
│       │   └── window_service.py
│       ├── infrastructure/     # Implementierungen
│       │   ├── config_loader.py
│       │   ├── keyboard_input_service.py
│       │   ├── kwin_focus_service.py
│       │   ├── mouse_input_service.py
│       │   ├── opencv_vision_service.py
│       │   └── touch_input_service.py
│       └── presentation/       # UI
│           └── main_window.py
├── config/
│   └── settings.yaml          # Hauptkonfiguration
├── templates/                 # OpenCV Templates für Zustandserkennung
├── calibrate_touch.py         # Touch-Kalibrierungs-Tool
├── debug_window.py            # Debug-Tool für Fensterinfo
├── main.py                    # Einstiegspunkt
└── pyproject.toml             # Projektkonfiguration
```

## Roadmap

- [x] Phase 1: Focus Detection
- [x] Phase 2: Window Detection
- [x] Phase 3: Touch Calibration
- [x] Phase 4: Virtueller Joystick (WASD)
- [x] Phase 5: Skill-Hotkeys (1-9)
- [ ] Phase 6: OpenCV State Detection
- [ ] Phase 7: Dynamische Keymaps
- [ ] Phase 8: Makros
- [ ] Phase 9: Profile

### Langfristige Features

- Skill Cooldown Detection
- HP/MP Detection
- Buff Detection
- Quest Detection
- Wayland Overlay
- Recording Mode

## Troubleshooting

### Touch funktioniert nicht
1. Prüfe Berechtigungen: `ls -la /dev/uinput`
2. Prüfe ob uinput-Modul geladen ist: `lsmod | grep uinput`
3. Starte mit sudo: `sudo env "PATH=$PATH" uv run python main.py`

### Touch kommt an falscher Position
1. Führe die Kalibrierung durch: `uv run python calibrate_touch.py`
2. Passe die Parameter in `config/settings.yaml` an
3. Siehe [Touch-Kalibrierung](#touch-kalibrierung)

### Waydroid wird nicht erkannt
1. Prüfe ob Waydroid läuft: `pgrep -f waydroid`
2. Prüfe den Fenstertitel: `kwin_wayland --list`
3. Passe die Erkennung in `kwin_focus_service.py` an

### OpenCV Template Matching funktioniert nicht
1. Prüfe ob Templates im `templates/` Verzeichnis sind
2. Prüfe die Bildschirmaufnahme-Berechtigungen
3. Teste mit: `spectacle -b -n -a -o /tmp/test.png`

## Beitragen

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/amazing-feature`)
3. Commit deine Änderungen (`git commit -m 'Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)
5. Öffne einen Pull Request

## Lizenz

Dieses Projekt ist für den persönlichen Gebrauch bestimmt.

## Danksagungen

- [Waydroid](https://docs.waydro.id/) - Android auf Linux
- [KDE Plasma](https://kde.org/plasma-desktop/) - Wayland Desktop
- [OpenCV](https://opencv.org/) - Computer Vision
- [evdev](https://python-evdev.readthedocs.io/) - Input Device Handling
