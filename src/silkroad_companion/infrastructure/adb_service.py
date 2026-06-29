"""
ADB-Service für die Abfrage von Android-Geräteinformationen.

Nutzt `adb` um:
- Die aktuelle Aktivität (Spiel/Menu/Chat) zu erkennen
- Die Display-Auflösung des Spiels abzufragen
- Die Fensterhierarchie zu analysieren
"""

import subprocess
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ADBService:
    """
    Service für ADB-basierte Abfragen von Android-Geräteinformationen.
    
    Voraussetzung: ADB muss installiert sein und das Gerät muss verbunden sein.
    """
    
    def __init__(self, serial: Optional[str] = None):
        """
        Initialisiert den ADB-Service.
        
        Args:
            serial: ADB-Serial-Nummer des Geräts (z. B. 'emulator-5554' für Waydroid).
                   Wenn None, wird das erste verfügbare Gerät verwendet.
        """
        self.serial = serial
        self._device_serial = self._get_device_serial()
    
    def _get_device_serial(self) -> Optional[str]:
        """Ermittelt die Serial-Nummer des Zielgeräts."""
        if self.serial:
            return self.serial
        
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                check=True
            )
            devices = []
            for line in result.stdout.strip().split("\n")[1:]:  # Überspringe Header
                if line.strip() and not line.startswith("*"):
                    parts = line.strip().split("\t")
                    if len(parts) >= 2 and parts[1] == "device":
                        devices.append(parts[0])
            
            if devices:
                # Priorisiere Waydroid-Geräte (meist 'emulator-5554' oder ähnlich)
                for device in devices:
                    if "emulator" in device or "waydroid" in device:
                        return device
                return devices[0]  # Erstes Gerät
        except Exception as e:
            logger.warning(f"Konnte ADB-Geräte nicht abfragen: {e}")
        
        return None
    
    def _run_adb_command(self, command: list[str]) -> Optional[str]:
        """Führt einen ADB-Befehl aus und gibt die Ausgabe zurück."""
        if not self._device_serial:
            logger.warning("Kein ADB-Gerät verfügbar")
            return None
        
        try:
            full_command = ["adb", "-s", self._device_serial] + command
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.warning("ADB-Befehl timeout")
            return None
        except subprocess.CalledProcessError as e:
            logger.warning(f"ADB-Befehl fehlgeschlagen: {e}")
            return None
        except Exception as e:
            logger.warning(f"Fehler beim ADB-Befehl: {e}")
            return None

    def get_current_activity(self) -> Optional[str]:
        """
        Gibt den Paketnamen und die Aktivität der aktuellen App zurück.
        
        Beispiel: 'com.silkroad.mb/com.silkroad.mb.MainActivity'
        """
        output = self._run_adb_command(["shell", "dumpsys", "window", "windows"])
        if not output:
            return None
        
        # Suche nach der aktuellen Fokus-Aktivität
        for line in output.split("\n"):
            if "mCurrentFocus" in line:
                # Beispiel: "  mCurrentFocus=Window{1234567 u0 com.silkroad.mb/com.silkroad.mb.MainActivity}"
                match = re.search(r'mCurrentFocus=Window\{[^}]*u(\d+) ([^}]+)\}', line)
                if match:
                    return match.group(2)
        
        return None

    def get_display_size(self) -> Optional[Tuple[int, int]]:
        """
        Gibt die Display-Auflösung des Geräts zurück (Breite, Höhe).
        
        Beispiel: (1280, 720)
        """
        output = self._run_adb_command(["shell", "dumpsys", "window"])
        if not output:
            return None
        
        # Suche nach mDisplaySize
        for line in output.split("\n"):
            if "mDisplaySize" in line:
                match = re.search(r'mDisplaySize=Point\((\d+), (\d+)\)', line)
                if match:
                    return int(match.group(1)), int(match.group(2))
        
        # Fallback: Versuche über wm size
        output = self._run_adb_command(["shell", "wm", "size"])
        if output:
            match = re.search(r'(\d+)x(\d+)', output.strip())
            if match:
                return int(match.group(1)), int(match.group(2))
        
        return None

    def get_window_size(self, activity: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """
        Gibt die Fenstergröße einer bestimmten Aktivität zurück.
        
        Args:
            activity: Paketname/Aktivität (z. B. 'com.silkroad.mb/com.silkroad.mb.MainActivity').
                     Wenn None, wird die aktuelle Aktivität verwendet.
        
        Beispiel: (1280, 720)
        """
        if not activity:
            activity = self.get_current_activity()
        
        if not activity:
            return None
        
        output = self._run_adb_command(["shell", "dumpsys", "window", "windows"])
        if not output:
            return None
        
        # Suche nach dem Fenster der Aktivität
        for line in output.split("\n"):
            if activity in line and "Window{" in line:
                # Beispiel: "  Window{1234567 u0 com.silkroad.mb/com.silkroad.mb.MainActivity}"
                # Wir brauchen die Größe, die in der nächsten Zeile oder im selben Block steht
                # Suche nach "Bounds" oder "Frame" in den folgenden Zeilen
                pass
        
        # Alternative: Nutze dumpsys window <activity>
        output = self._run_adb_command(["shell", "dumpsys", "window", activity.split("/")[0]])
        if not output:
            return None
        
        # Suche nach mFrame oder mBounds
        for line in output.split("\n"):
            if "mFrame=" in line:
                match = re.search(r'mFrame=\[(\d+),(\d+)\[(\d+),(\d+)\]]', line)
                if match:
                    return int(match.group(3)) - int(match.group(1)), int(match.group(4)) - int(match.group(2))
            elif "mBounds=" in line:
                match = re.search(r'mBounds=\[(\d+),(\d+)\[(\d+),(\d+)\]]', line)
                if match:
                    return int(match.group(3)) - int(match.group(1)), int(match.group(4)) - int(match.group(2))
        
        return None

    def is_waydroid_running(self) -> bool:
        """Prüft, ob Waydroid läuft."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "waydroid"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_waydroid_serial(self) -> Optional[str]:
        """Gibt die ADB-Serial-Nummer des Waydroid-Geräts zurück."""
        if self._device_serial and ("emulator" in self._device_serial or "waydroid" in self._device_serial):
            return self._device_serial
        return None
