import logging
import os
import subprocess
import tempfile
import threading
from typing import Any, Optional

from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusReply

from silkroad_companion.domain.focus_service import FocusService
from silkroad_companion.domain.window_service import WindowService
from silkroad_companion.domain.models import WindowInfo

logger = logging.getLogger(__name__)

KWIN_SCRIPT = """
function logWindow(window) {
    if (window) {
        console.log("SRO_FOCUS_CLASS:" + window.resourceClass);
        console.log("SRO_FOCUS_TITLE:" + window.caption);
        console.log("SRO_GEOMETRY:" + window.x + "," + window.y + "," + window.width + "," + window.height);
    } else {
        console.log("SRO_FOCUS_CLASS:none");
        console.log("SRO_FOCUS_TITLE:none");
        console.log("SRO_GEOMETRY:0,0,0,0");
    }
}

workspace.windowActivated.connect(logWindow);

// Initial
logWindow(workspace.activeWindow);
"""

class KWinFocusService(FocusService, WindowService):
    def __init__(self) -> None:
        self._current_focus_class = ""
        self._current_window_title = ""
        self._current_geometry = (0, 0, 0, 0)
        self._script_name = "sro_focus_tracker"
        self._stop_event = threading.Event()

        self._setup_kwin_script()
        self._start_journal_monitor()

    def _setup_kwin_script(self) -> None:
        try:
            bus = QDBusConnection.sessionBus()
            iface = QDBusInterface("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", bus)

            # Altes Script entladen falls vorhanden
            iface.call("unloadScript", self._script_name)

            # Temporäre Datei für das Script erstellen
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(KWIN_SCRIPT)
                script_path = f.name

            # Script laden
            reply = QDBusReply(iface.call("loadScript", script_path, self._script_name))
            if reply.isValid():
                iface.call("start")
                logger.info("KWin Fokus-Tracker Script geladen.")
            else:
                logger.error(f"KWin Script Fehler: {reply.error().message()}")

            os.unlink(script_path)
        except Exception as e:
            logger.error(f"Fehler beim Setup des KWin Scripts: {e}")

    def _start_journal_monitor(self) -> None:
        def monitor() -> None:
            # Wir überwachen das Journal auf SRO_FOCUS_CLASS
            # Wir nutzen -n 0 um nur neue Einträge zu bekommen
            process = subprocess.Popen(
                ["journalctl", "--user", "-f", "-n", "0", "-o", "cat"],
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
