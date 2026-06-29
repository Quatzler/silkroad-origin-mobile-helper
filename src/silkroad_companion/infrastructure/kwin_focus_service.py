import logging
import os
import subprocess
import tempfile
import threading
from typing import Any, Optional

from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusReply, QDBusMessage

from silkroad_companion.domain.focus_service import FocusService
from silkroad_companion.domain.window_service import WindowService
from silkroad_companion.domain.models import WindowInfo

logger = logging.getLogger(__name__)

KWIN_SCRIPT = """
function logWindow(window) {
    if (window) {
        var resClass = window.resourceClass ? window.resourceClass.toString() : "";
        var caption = window.caption ? window.caption.toString() : "";
        console.log("SRO_FOCUS_CLASS:" + resClass);
        console.log("SRO_FOCUS_TITLE:" + caption);
        console.log("SRO_GEOMETRY:" + Math.round(window.x) + "," + Math.round(window.y) + "," + Math.round(window.width) + "," + Math.round(window.height));
        console.log("SRO_CURSOR:" + Math.round(workspace.cursorPos.x) + "," + Math.round(workspace.cursorPos.y));
    } else {
        console.log("SRO_FOCUS_CLASS:none");
        console.log("SRO_FOCUS_TITLE:none");
        console.log("SRO_GEOMETRY:0,0,0,0");
        console.log("SRO_CURSOR:0,0");
    }
}

workspace.windowActivated.connect(logWindow);

function setupWindow(window) {
    if (window) {
        var resClass = window.resourceClass ? window.resourceClass.toString() : "";
        if (resClass.indexOf("waydroid") !== -1) {
            // In KWin 6 heißt es frameGeometryChanged
            if (window.frameGeometryChanged) {
                window.frameGeometryChanged.connect(function() {
                    logWindow(window);
                });
            } else if (window.geometryChanged) {
                window.geometryChanged.connect(function() {
                    logWindow(window);
                });
            }
        }
    }
}

workspace.windowAdded.connect(setupWindow);
workspace.windowList().forEach(setupWindow);

// Initial
logWindow(workspace.activeWindow);
"""

class KWinFocusService(FocusService, WindowService):
    def __init__(self) -> None:
        self._current_focus_class = ""
        self._current_window_title = ""
        self._current_geometry = (0, 0, 0, 0)
        self._current_cursor_pos = (0, 0)
        self._script_name = "sro_focus_tracker"
        self._stop_event = threading.Event()

        self._setup_kwin_script()
        self._start_journal_monitor()

    def _setup_kwin_script(self) -> None:
        try:
            bus = QDBusConnection.sessionBus()
            iface = QDBusInterface("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", bus)
            if not iface.isValid():
                # Fallback auf großgeschriebene Variante probieren
                logger.debug("Versuche Fallback auf org.kde.KWin.Scripting")
                iface = QDBusInterface("org.kde.KWin", "/Scripting", "org.kde.KWin.Scripting", bus)

            if not iface.isValid():
                logger.error(f"KWin Scripting Interface konnte nicht gefunden werden: {iface.lastError().message()}")
                return

            # Altes Script entladen falls vorhanden
            iface.call("unloadScript", self._script_name)

            # Temporäre Datei für das Script erstellen
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(KWIN_SCRIPT)
                script_path = f.name

            # Script laden
            reply = iface.call("loadScript", script_path, self._script_name)
            if reply.type() == QDBusMessage.ReplyMessage:
                script_id = reply.arguments()[0]
                # Das Script-Objekt liegt unter /Scripting/Script{id}
                script_path_dbus = f"/Scripting/Script{script_id}"
                script_iface = QDBusInterface("org.kde.KWin", script_path_dbus, "org.kde.kwin.Script", bus)
                if not script_iface.isValid():
                    # Fallback Interface Name
                    script_iface = QDBusInterface("org.kde.KWin", script_path_dbus, "org.kde.KWin.Script", bus)

                if script_iface.isValid():
                    script_iface.call("run")
                    logger.info(f"KWin Fokus-Tracker Script geladen und gestartet (ID: {script_id}).")
                else:
                    logger.error(f"KWin Script Objekt konnte nicht gefunden werden unter {script_path_dbus}")
            else:
                logger.error(f"KWin Script Lade-Fehler: {reply.errorMessage()}")

            os.unlink(script_path)
        except Exception as e:
            logger.error(f"Fehler beim Setup des KWin Scripts: {e}")

    def _start_journal_monitor(self) -> None:
        def monitor() -> None:
            # Wir überwachen das Journal auf SRO_FOCUS_CLASS
            # Wir nutzen -n 0 um nur neue Einträge zu bekommen
            process = subprocess.Popen(
                ["journalctl", "--user", "-f", "-n", "5", "-o", "cat"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            # Damit wir nicht hängen bleiben, wenn das Journal keine Daten liefert
            if process.stdout:
                while not self._stop_event.is_set():
                    line = process.stdout.readline()
                    if not line:
                        break
                    self._parse_line(line)
                process.terminate()

        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()

    def _parse_line(self, line: str) -> None:
        if "SRO_FOCUS_CLASS:" in line:
            self._current_focus_class = line.split("SRO_FOCUS_CLASS:")[1].strip()
        elif "SRO_FOCUS_TITLE:" in line:
            self._current_window_title = line.split("SRO_FOCUS_TITLE:")[1].strip()
        elif "SRO_GEOMETRY:" in line:
            try:
                geom_str = line.split("SRO_GEOMETRY:")[1].strip()
                # Koordinaten können Floats sein (z.B. bei Skalierung), wir brauchen Ints
                self._current_geometry = tuple(map(lambda x: int(float(x)), geom_str.split(",")))
            except (ValueError, IndexError):
                logger.error(f"Fehler beim Parsen der Geometrie: {line.strip()}")
        elif "SRO_CURSOR:" in line:
            try:
                cursor_str = line.split("SRO_CURSOR:")[1].strip()
                self._current_cursor_pos = tuple(map(lambda x: int(float(x)), cursor_str.split(",")))
            except (ValueError, IndexError):
                pass

    def is_waydroid_active(self) -> bool:
        try:
            result = subprocess.run(["pgrep", "-f", "waydroid"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def is_waydroid_focused(self) -> bool:
        # Wir prüfen auf die spezifische Silkroad Klasse
        # Der User meldete: waydroid.com.silkroad.mb
        target = "waydroid.com.silkroad.mb"
        is_focused = (
            target in self._current_focus_class.lower()
            or "waydroid" in self._current_focus_class.lower()
        )
        return is_focused

    def get_active_window_title(self) -> str | None:
        return self._current_window_title if self._current_window_title else None

    def get_window_info(self) -> WindowInfo:
        x, y, w, h = self._current_geometry
        return WindowInfo(
            x=x,
            y=y,
            width=w,
            height=h,
            focused=self.is_waydroid_focused(),
            dpi=1.0  # TODO: Implementiere DPI Erkennung
        )

    def get_cursor_pos(self) -> tuple[int, int]:
        return self._current_cursor_pos
