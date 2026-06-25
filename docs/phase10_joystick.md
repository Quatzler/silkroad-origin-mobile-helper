# Phase 10: Joystick & Erweiterte Konfiguration

In dieser Phase wurden zwei wesentliche Verbesserungen implementiert:
1. **Konfigurierbare Klick-Koordinaten**: Keybindings in der `settings.yaml` können nun optionale `x` und `y` Werte enthalten. Wenn diese vorhanden sind, führt die Mapping Engine einen relativen Klick an dieser Position aus, anstatt die Standard-Logik für die Aktion zu nutzen.
2. **Virtueller Joystick (WASD)**: Unterstützung für Bewegungen via WASD. Dies simuliert das Drücken und Halten der entsprechenden Richtungen auf dem virtuellen Joystick von Silkroad Mobile.

## Implementierungsdetails

### Konfigurations-Erweiterung
Die `KeyBind`-Klasse wurde um `x` und `y` Felder erweitert.
Beispiel:
```yaml
"1":
  action: "skill_1"
  x: 0.6
  y: 0.9
```

### Input-System (Key-Up Support)
Das `InputService`-Interface und die `KeyboardInputService`-Implementierung (evdev) wurden erweitert, um sowohl Tastendruck- als auch Loslass-Events zu unterstützen. Dies ist essenziell für die Joystick-Steuerung, damit der Charakter beim Loslassen der Taste aufhört zu laufen.

### Maus-System (Hold Support)
`MouseService` unterstützt nun `press_relative` und `release_relative`. Dies erlaubt es, die linke Maustaste an einer Position gedrückt zu halten, was für die Joystick-Simulation notwendig ist.

### Joystick-Logik
In der `MappingEngine` wurde die Methode `_handle_joystick` hinzugefügt. Sie berechnet basierend auf einem (derzeit noch fixen) Joystick-Zentrum (`0.15, 0.75`) die Zielkoordinaten für die Richtungen W, A, S und D.

## Risiken
- **Joystick-Position**: Die Position des Joysticks kann je nach Gerätelayout leicht variieren. In einer späteren Phase könnte diese ebenfalls konfigurierbar gemacht werden.
- **Multitouch**: Derzeit wird nur ein virtueller "Finger" (die Maus) simuliert. Gleichzeitiges Drücken mehrerer Skill-Buttons während der Bewegung ist mit dieser Methode nicht möglich (da Silkroad Mobile Multitouch nutzt, wir aber nur eine Maus haben).
