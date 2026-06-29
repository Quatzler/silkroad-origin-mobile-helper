# Touchscreen Kalibrierung

## Problem

Die Touch-Events landen nicht an der erwarteten Position im Waydroid-Fenster. Dies liegt daran, dass die Koordinatentransformation zwischen Desktop-Pixel und uinput-Touchscreen nicht perfekt kalibriert ist.

## Ursache

Wayland/KWin hat eine eigene Kalibrierung für Touch-Events, die sich von der reinen Pixel-Position unterscheiden kann. Die uinput-Device sendet Koordinaten im Bereich 0-32767, aber die Mapping von Desktop-Pixel zu diesen Koordinaten muss angepasst werden.

## Lösung: Kalibrierungsparameter

Füge folgende Konfiguration zu deiner `config/settings.yaml` hinzu:

```yaml
touch_calibration:
  scale_x: 1.0    # Skalierungsfaktor X-Achse
  scale_y: 1.0    # Skalierungsfaktor Y-Achse
  offset_x: 0     # Pixel-Offset X-Achse
  offset_y: 0     # Pixel-Offset Y-Achse
```

## Kalibrierungs-Tool

Das Projekt enthält ein interaktives Kalibrierungs-Tool:

```bash
uv run python calibrate_touch.py
```

### Verwendung:

1. **Starte das Kalibrierungs-Tool**
2. **Stelle sicher, dass Silkroad Origin Mobile in Waydroid läuft und fokussiert ist**
3. **Teste verschiedene Positionen:**
   - Gib relative Koordinaten ein (0.0 - 1.0)
   - Klicke auf "Test Position"
   - Beobachte, wo der Touch im Spiel ankommt
4. **Passe die Kalibrierungsparameter an:**
   - `scale_x/y`: Skaliert die Koordinaten (1.0 = keine Skalierung)
   - `offset_x/y`: Verschiebt die Koordinaten um Pixel
5. **Kopiere die generierte YAML-Konfiguration** in deine `settings.yaml`

## Manuelle Kalibrierung

### Schritt 1: Testpositionen finden

Führe folgende Tests durch und notiere die Abweichungen:

```bash
# Teste die Mitte des Fensters
uv run python -c "
import sys; sys.path.insert(0, 'src')
from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
from silkroad_companion.domain.models import WindowInfo

touch = EvdevTouchService()
focus = KWinFocusService()

# Screen Size setzen (anpassen an deine Auflösung)
touch.set_screen_size(4054, 1200, 0, 0)

# Fenster-Info holen
info = focus.get_window_info()
print(f'Fenster: {info.width}x{info.height} @ ({info.x}, {info.y})')

# Mitte testen
touch.click_relative(0.5, 0.5, info, slot=0)
print('Touch bei (0.5, 0.5) ausgeführt - wo kommt er an?')
"
```

### Schritt 2: Abweichung messen

Angenommen:
- **Erwartet:** Touch bei (0.5, 0.5) = Mitte des Fensters
- **Tatsächlich:** Touch kommt bei 45% von links und 55% von oben an

Dann brauchst du:
- `scale_x: 1.11` (weil 0.5 / 0.45 ≈ 1.11)
- `scale_y: 0.91` (weil 0.5 / 0.55 ≈ 0.91)

### Schritt 3: Offset berechnen

Wenn der Touch systematisch um einige Pixel verschoben ist:
- **Erwartet:** (100, 100)
- **Tatsächlich:** (105, 95)
- **Offset:** `offset_x: -5, offset_y: 5`

## Beispiel-Konfigurationen

### Beispiel 1: Standard (keine Kalibrierung)
```yaml
touch_calibration:
  scale_x: 1.0
  scale_y: 1.0
  offset_x: 0
  offset_y: 0
```

### Beispiel 2: Leichte Skalierung
```yaml
touch_calibration:
  scale_x: 0.97
  scale_y: 0.95
  offset_x: 12
  offset_y: -6
```

### Beispiel 3: Dual-Monitor Setup
```yaml
touch_calibration:
  scale_x: 1.05
  scale_y: 0.98
  offset_x: -20
  offset_y: 10
```

## Tipps

1. **Starte mit scale_x = scale_y = 1.0** und offset_x = offset_y = 0
2. **Teste zuerst die Ecken:** (0,0), (1,1), (0.5, 0.5)
3. **Passe zuerst die Skalierung an**, dann den Offset
4. **Kleine Änderungen:** Ändere die Werte in Schritten von 0.01 für scale und 1-2 Pixel für offset
5. **Teste mit verschiedenen Fenstergrößen**, falls Waydroid fensterbar ist

## Debugging

Aktiviere den Debug-Modus in der Konfiguration:

```yaml
debug_mode: true
```

Dann siehst du detaillierte Logs über die Koordinatentransformation:

```
Touch-Mapping: Rel (0.5, 0.5) -> Abs Pixel (1000, 500)
Touch-Mapping: Kalibriert (1000, 500)
Touch-Mapping: uinput coords (16383, 8191)
```

## Technischer Hintergrund

Die Transformation funktioniert so:

```
Relativ (x, y) 
  → Absolut Pixel: window.x + window.width * x, window.y + window.height * y
  → Kalibriert: (pixel_x * scale_x) + offset_x, (pixel_y * scale_y) + offset_y
  → uinput: ((calibrated_x - offset_x) / screen_width) * 32767
```

Die uinput-Device hat einen Bereich von 0-32767 für X und Y. Die Kalibrierung passt die Desktop-Pixel an diesen Bereich an.

## Häufige Probleme

### Problem: Touch kommt immer an der gleichen Position an
- **Ursache:** uinput-Device wurde nicht korrekt erstellt
- **Lösung:** Prüfe Berechtigungen (`/dev/uinput` muss beschreibbar sein)

### Problem: Touch ist spiegelverkehrt
- **Ursache:** Falsche Skalierungsfaktoren
- **Lösung:** Versuche negative scale-Werte oder prüfe die Monitor-Konfiguration

### Problem: Touch funktioniert nur in einem Bereich
- **Ursache:** Falsche screen_width/height
- **Lösung:** Prüfe die Gesamt-Desktop-Größe mit `xrandr` oder `kwin_wayland`

### Problem: Touch ist zu ungenau
- **Ursache:** Zu große uinput-Bereich (32767)
- **Lösung:** Versuche kleinere max_x/max_y Werte im TouchService

## Erweitert: Dynamische Kalibrierung

Für fortgeschrittene User kann die Kalibrierung auch dynamisch angepasst werden, basierend auf der Fensterposition:

```python
# In main.py oder einem Custom-Service
class DynamicCalibrationService:
    def __init__(self, touch_service, window_tracker):
        self.touch_service = touch_service
        self.window_tracker = window_tracker
        self.window_tracker.subscribe(self.update_calibration)
    
    def update_calibration(self, window_info: WindowInfo):
        # Anpassen der Kalibrierung basierend auf Fensterposition
        if window_info.x > 2000:  # Fenster auf zweitem Monitor
            self.touch_service.set_calibration(
                scale_x=1.05, scale_y=0.98, offset_x=-20, offset_y=10
            )
        else:
            self.touch_service.set_calibration(
                scale_x=1.0, scale_y=1.0, offset_x=0, offset_y=0
            )
```

Dies ist besonders nützlich für Multi-Monitor-Setups.
