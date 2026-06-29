# Zusammenfassung der Änderungen

## 🎯 Hauptziele

1. **Touch-Kalibrierung implementieren** - Lösung für Problem: "Touch landet an falscher Position"
2. **Gleichzeitige Maus- und Touch-Steuerung ermöglichen** - Lösung für Problem: "Maus und Touch dürfen sich nicht beeinflussen"

## 📋 Änderungen im Detail

### 1. Neue Konfigurationsoptionen (`domain/config.py`)

**Hinzugefügt:**
```python
class TouchCalibration(BaseModel):
    """Kalibrierung für den virtuellen Touchscreen."""
    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: int = 0
    offset_y: int = 0

class AppConfig(BaseModel):
    # ... bestehende Felder ...
    touch_calibration: TouchCalibration = TouchCalibration()
```

**Zweck:** Ermöglicht feine Anpassung der Touch-Positionen via YAML-Konfiguration.

### 2. Erweiterter Touch-Service (`infrastructure/touch_input_service.py`)

**Hinzugefügt:**
- `set_calibration()` Methode zur Konfiguration der Kalibrierungsparameter
- Kalibrierungsparameter: `calibration_scale_x/y`, `calibration_offset_x/y`
- Verbessertes Logging für Debugging

**Geändert:**
- `_get_abs_coords()` wendet nun Kalibrierung an:
  ```python
  # Kalibrierung anwenden
  calibrated_x = (abs_px_x * self.calibration_scale_x) + self.calibration_offset_x
  calibrated_y = (abs_px_y * self.calibration_scale_y) + self.calibration_offset_y
  ```

**Zweck:** Präzise Touch-Positionierung durch Skalierung und Offset-Korrektur.

### 3. Hauptanwendung (`main.py`)

**Geändert:**
- Lädt Touch-Kalibrierung aus Config:
  ```python
  if total_rect:
      touch_service.set_screen_size(
          total_rect.width(),
          total_rect.height(),
          total_rect.x(),
          total_rect.y()
      )
      touch_service.set_calibration(config.touch_calibration)
  ```

**Zweck:** Automatische Anwendung der Kalibrierung beim Start.

### 4. Mapping Engine (`application/mapping_engine.py`)

**Geändert:**
- Verbesserte Kommentare und Logging
- Klare Trennung zwischen Touch-Slots:
  - **Slot 0**: Klicks (Skills, Buttons)
  - **Slot 1**: Joystick (Bewegung)
  - **Slots 2-9**: Reserviert für zukünftige Nutzung

**Zweck:** Ermöglicht gleichzeitige Nutzung von Maus (für Kamera) und Touch (für Bewegung/Skills).

### 5. Neue Tools

#### `calibrate_touch.py`
Interaktives GUI-Tool zur Touch-Kalibrierung:
- Testet verschiedene Touch-Positionen
- Ermöglicht Anpassung der Kalibrierungsparameter
- Generiert YAML-Konfiguration

**Verwendung:**
```bash
uv run python calibrate_touch.py
```

#### `debug_window.py`
Debug-Tool zur Anzeige von Fenstergeometrie und Touch-Koordinaten:
- Zeigt Echtzeit-Fensterinformationen
- Berechnet Testpositionen
- Zeigt uinput-Koordinaten an

**Verwendung:**
```bash
uv run python debug_window.py
```

### 6. Dokumentation

**Hinzugefügt:**
- `docs/TOUCH_CALIBRATION.md` - Ausführliche Anleitung zur Touch-Kalibrierung
- Aktualisierte `README.md` mit neuen Features und Anleitungen

## 🔄 Migrationsguide

### Für bestehende Nutzer

1. **Kalibrierung durchführen (WICHTIG!)**
   ```bash
   uv run python calibrate_touch.py
   ```
   Folge den Anweisungen und kopiere die generierte Konfiguration.

2. **Konfiguration aktualisieren**
   Füge die Touch-Kalibrierung zu deiner `config/settings.yaml` hinzu:
   ```yaml
   touch_calibration:
     scale_x: 1.0
     scale_y: 1.0
     offset_x: 0
     offset_y: 0
   ```

3. **Testen**
   Starte die Anwendung und prüfe, ob die Touch-Positionen jetzt korrekt sind.

### Für Entwickler

1. **Neue Abhängigkeiten:** Keine neuen Python-Pakete nötig
2. **API-Änderungen:**
   - `TouchService.set_calibration()` ist neu
   - `AppConfig.touch_calibration` ist neu
3. **Breaking Changes:** Keine - alle Änderungen sind rückwärtskompatibel

## 🎯 Lösung der Hauptprobleme

### Problem 1: Touch landet an falscher Position

**Lösung:**
- Kalibrierungssystem mit Skalierung und Offset
- Interaktives Kalibrierungs-Tool
- Debug-Tool für manuelle Analyse

**Implementation:**
```python
# In touch_input_service.py
def _get_abs_coords(self, x: float, y: float, window_info: WindowInfo) -> tuple[int, int]:
    abs_px_x = window_info.x + (window_info.width * x)
    abs_px_y = window_info.y + (window_info.height * y)
    
    # Kalibrierung anwenden
    calibrated_x = (abs_px_x * self.calibration_scale_x) + self.calibration_offset_x
    calibrated_y = (abs_px_y * self.calibration_scale_y) + self.calibration_offset_y
    
    # Skalierung auf uinput-Bereich
    tx = int(((calibrated_x - self.offset_x) / self.screen_width) * self.max_x)
    ty = int(((calibrated_y - self.offset_y) / self.screen_height) * self.max_y)
    
    return tx, ty
```

### Problem 2: Gleichzeitige Maus- und Touch-Steuerung

**Lösung:**
- Separate Touch-Slots für verschiedene Zwecke
- Slot 0: Klicks (Skills, Buttons)
- Slot 1: Joystick (Bewegung)
- Maus bleibt System-Maus (für Kamera)

**Implementation:**
```python
# In mapping_engine.py
def _handle_joystick(self, action: str, is_down: bool, window_info: WindowInfo) -> None:
    # Nutzt Slot 1 für Joystick
    self.touch_service.press_relative(center_x, center_y, window_info, slot=1)
    self.touch_service.move_relative(target_x, target_y, window_info, slot=1)
    self.touch_service.release_relative(slot=1)

def _execute_action(self, key: str, bind: KeyBind, is_down: bool) -> None:
    # Nutzt Slot 0 für Klicks
    self.touch_service.click_relative(bind.x, bind.y, window_info, slot=0)
```

## 📊 Technische Details

### Touch-Koordinatentransformation

```
Relativ (x, y) 
  → Absolut Pixel: window.x + window.width * x, window.y + window.height * y
  → Kalibriert: (pixel_x * scale_x) + offset_x, (pixel_y * scale_y) + offset_y
  → uinput: ((calibrated_x - offset_x) / screen_width) * 32767
```

### Multi-Touch Slots

| Slot | Verwendung | Beschreibung |
|------|------------|--------------|
| 0 | Klicks | Skills, Buttons, einzelne Touches |
| 1 | Joystick | Bewegung (WASD), Swipe-Gesten |
| 2-9 | Reserviert | Für zukünftige Features |

### Berechtigungen

Die Anwendung benötigt:
- `/dev/uinput` - Schreibzugriff für virtuelle Touch-Device
- `/dev/input/event*` - Lesezugriff für Tastatur/Maus-Events

**Setup:**
```bash
# udev-Regel erstellen
sudo nano /etc/udev/rules.d/99-silkroad.rules
```

Inhalt:
```text
KERNEL=="uinput", GROUP="input", MODE="0660"
KERNEL=="event*", GROUP="input", MODE="0660"
```

Dann:
```bash
sudo usermod -aG input $USER
sudo reboot
```

## 🚀 Nächste Schritte

### Für Nutzer

1. Kalibrierung durchführen
2. Konfiguration anpassen
3. Anwendung testen
4. Feedback geben

### Für Entwickler

1. OpenCV State Detection implementieren
2. Dynamische Keymaps fertigstellen
3. Makro-System implementieren
4. Profile-System implementieren
5. Overlay für Wayland entwickeln

## 📝 Changelog

### Version 0.2.0 (in Entwicklung)

**Neue Features:**
- Touch-Kalibrierungssystem
- Kalibrierungs-Tool (GUI)
- Debug-Tool für Fensterinfo
- Multi-Slot Touch-Unterstützung
- Gleichzeitige Maus- und Touch-Steuerung

**Verbesserungen:**
- Verbessertes Logging
- Bessere Fehlerbehandlung
- Aktualisierte Dokumentation

**Bugfixes:**
- Touch-Positionen werden nun korrekt kalibriert
- Joystick und Klicks stören sich nicht mehr gegenseitig

### Version 0.1.0

- Initiales Release
- Grundlegende Focus Detection
- Window Tracking
- Touch-Input (ohne Kalibrierung)
- Mapping Engine (Grundfunktionalität)
