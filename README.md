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

### Tests ausführen

```bash
uv run pytest
```

### Linting & Typ-Check

```bash
uv run ruff check .
uv run mypy src
```
