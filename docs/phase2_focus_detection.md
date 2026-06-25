# Phase 2: Focus Detection

## Architekturentscheidung

Die Fokus-Erkennung wurde über eine abstrakte Schnittstelle `FocusService` im Domain-Layer entkoppelt. Die konkrete Implementierung `KWinFocusService` nutzt die DBus-Schnittstelle von KDE Plasma 6 (KWin).

Vorteil: Sollte die Anwendung auf ein anderes Desktop-System portiert werden, muss lediglich eine neue Implementierung des `FocusService` erstellt werden.

Die Erkennung erfolgt über `org.kde.KWin.queryWindowInfo`, welches unter Plasma 6 zuverlässig Informationen über das aktuell fokussierte Fenster liefert, ohne dass komplexe Wayland-Protokolle direkt implementiert werden müssen.

## Implementierung (Update)

Die Fokus-Erkennung unter KDE Plasma 6 Wayland wurde aufgrund restriktiver Sicherheitsrichtlinien über einen hybriden Ansatz realisiert:

1.  **KWin Scripting**: Ein leichtgewichtiges JavaScript wird in KWin geladen, das auf das Signal `workspace.windowActivated` hört. Dieses Signal liefert zuverlässig Informationen über das aktuell fokussierte Fenster, ohne dass der Benutzer manuell ein Fenster auswählen muss (kein Freeze mehr).
2.  **Journal-Kommunikation**: Da KWin-Scripte keinen direkten Dateizugriff haben, schreibt das Script Status-Änderungen mittels `console.log` in das System-Journal.
3.  **Journal Monitoring**: Der `KWinFocusService` startet einen Hintergrund-Thread, der das Journal in Echtzeit überwacht (`journalctl -f`) und die Fokus-Informationen extrahiert.
4.  **Waydroid Erkennung**: Das System erkennt nun spezifisch die Fensterklasse `waydroid.com.silkroad.mb`, die vom Benutzer identifiziert wurde.

## Vorteile

*   **Nicht-blockierend**: Keine interaktiven DBus-Abfragen mehr, das System bleibt voll bedienbar.
*   **Echtzeit**: Fokuswechsel werden nahezu verzögerungsfrei erkannt.
*   **Präzise**: Unterscheidung zwischen Waydroid allgemein und der Silkroad-App ist möglich.

## Risiken

*   **DBus-Verfügbarkeit**: Falls KWin nicht läuft oder DBus blockiert ist, schlägt die Erkennung fehl. Dies wird über Logging abgefangen.
*   **Waydroid-Identifizierung**: Aktuell wird nach "waydroid" im `desktopFile` oder der `resourceClass` gesucht. Sollten zukünftige Waydroid-Versionen diese IDs ändern, muss der Filter angepasst werden.

## Testergebnisse

*   Unit Tests mit Mock-Services erfolgreich.
*   Manuelle Prüfung der DBus-Schnittstelle lieferte korrekte Fensterdaten für Waydroid.
