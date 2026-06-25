# Silkroad Companion

Silkroad Companion ist ein spezialisiertes Linux-Desktop-Tool zur Steuerung von Silkroad Origin Mobile auf Waydroid unter KDE Plasma 6.

## Features (geplant)

* Focus Detection (Waydroid & Silkroad)
* Window Tracking (Relative Koordinaten)
* Vision Engine (Zustandserkennung via OpenCV)
* Mapping Engine (YAML-basierte Steuerung)
* State Engine (Validierte Spielzustände)

## Entwicklung

Dieses Projekt verwendet `uv` für das Paketmanagement.

### Voraussetzungen

* Python 3.13+
* KDE Plasma 6 (Wayland)
* Waydroid

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

### Tests ausführen

```bash
uv run pytest
```

### Linting & Typ-Check

```bash
uv run ruff check .
uv run mypy src
```
