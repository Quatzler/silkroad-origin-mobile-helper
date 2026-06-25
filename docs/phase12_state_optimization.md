# Phase 12: Optimierung der Zustandserkennung

In dieser Phase wurde die Vision Engine erweitert, um neue Spielzustände präziser zu erkennen und die Benutzererfahrung zu verbessern.

## Änderungen

1. **Zustands-Erweiterung**:
   * Der Zustand `INVENTORY` wurde in `MENU` umbenannt, um allgemeine Menüs (erkannt am Back-Button) besser abzubilden.
   * Ein neuer Zustand `CHAT` wurde hinzugefügt, um den Chat-Modus spezifisch zu behandeln.
2. **Priorisierte Erkennung**:
   * Die Vision Engine prüft nun in einer optimierten Reihenfolge: `MENU` -> `CHAT` -> `LOGIN` -> `GAME`.
   * Dies stellt sicher, dass Überlagerungen (wie das Chat-Fenster oder Menüs über dem Spiel) korrekt priorisiert werden.
3. **Template-Matching**:
   * Das System nutzt nun `templates/chat/chat.jpg` für die Chat-Erkennung.
   * Der Back-Button wird nun im Ordner `templates/menu` verwaltet.
4. **Konfigurations-Update**:
   * Die `settings.yaml` wurde aktualisiert, um die neuen Zustände `menu` und `chat` zu unterstützen.
   * Beide Zustände verfügen nun standardmäßig über ein ESC-Mapping für den Back-Button.

## Verifizierung

* **Automatisierte Tests**: Alle 25 Tests (einschließlich der aktualisierten Vision- und Mapping-Tests) wurden erfolgreich ausgeführt.
* **Manuelle Validierung**: Die Verzeichnisstruktur wurde an die neuen Zustände angepasst und die Template-Ladeprozesse verifiziert.

## Benutzung
Die Anwendung erkennt nun automatisch, wenn Sie sich im Chat oder in einem Menü befinden. Die GUI zeigt den aktuellen State (`CHAT`, `MENU`, `GAME`) live an.
