import logging
import evdev
from evdev import ecodes, UInput
from silkroad_companion.domain.input_service import MouseService
from silkroad_companion.domain.models import WindowInfo
import time

logger = logging.getLogger(__name__)

class EvdevMouseService(MouseService):
    def __init__(self) -> None:
        self._ui = self._create_uinput_device()

    def _create_uinput_device(self) -> UInput | None:
        try:
            # Wir erstellen eine virtuelle Maus für Klicks
            capabilities = {
                ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE],
            }
            ui = UInput(capabilities, name="Silkroad-Companion-Virtual-Clicker")
            logger.info("Virtueller Klicker via uinput erstellt.")
            return ui
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des uinput Geräts: {e}")
            return None

    def click_relative(self, x: float, y: float, window_info: WindowInfo) -> None:
        if not window_info or window_info.width == 0:
            logger.warning("Klick abgebrochen: Keine Fensterinformationen.")
            return

        abs_x = int(window_info.x + (window_info.width * x))
        abs_y = int(window_info.y + (window_info.height * y))

        # 1. Cursor bewegen (Lokaler Import von pynput, um Testprobleme zu vermeiden)
        try:
            from pynput.mouse import Controller
            mouse = Controller()
            mouse.position = (abs_x, abs_y)
            time.sleep(0.05)
        except Exception as e:
            logger.warning(f"Fehler beim Bewegen des Cursors: {e}")

        # 2. Klick via uinput senden
        if self._ui:
            try:
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1) # Down
                self._ui.syn()
                time.sleep(0.05)
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0) # Up
                self._ui.syn()
                logger.info(f"Klick via uinput bei ({abs_x}, {abs_y})")
            except Exception as e:
                logger.error(f"Fehler beim Senden des uinput-Klicks: {e}")
        else:
            logger.warning("uinput Gerät nicht vorhanden, sende Klick via pynput (Fallback)")
            try:
                from pynput.mouse import Button, Controller
                mouse = Controller()
                mouse.click(Button.left, 1)
            except Exception as e:
                logger.error(f"Fallback-Klick fehlgeschlagen: {e}")

    def move_relative(self, x: float, y: float, window_info: WindowInfo) -> None:
        abs_x = int(window_info.x + (window_info.width * x))
        abs_y = int(window_info.y + (window_info.height * y))
        try:
            from pynput.mouse import Controller
            mouse = Controller()
            mouse.position = (abs_x, abs_y)
        except:
            pass
