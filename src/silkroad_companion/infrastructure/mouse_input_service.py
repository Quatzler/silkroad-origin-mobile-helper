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
        self.press_relative(x, y, window_info)
        time.sleep(0.05)
        self.release_relative(x, y, window_info)

    def press_relative(self, x: float, y: float, window_info: WindowInfo) -> None:
        if not window_info or window_info.width == 0:
            return

        abs_x = int(window_info.x + (window_info.width * x))
        abs_y = int(window_info.y + (window_info.height * y))

        # Cursor bewegen
        self.move_relative(x, y, window_info)
        time.sleep(0.02)

        # Down via uinput
        if self._ui:
            try:
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1) # Down
                self._ui.syn()
                logger.debug(f"Maus-Down bei ({abs_x}, {abs_y})")
            except Exception as e:
                logger.error(f"Fehler beim Senden des uinput-Down: {e}")
        else:
            try:
                from pynput.mouse import Button, Controller
                mouse = Controller()
                mouse.press(Button.left)
            except Exception as e:
                logger.error(f"Fallback-Down fehlgeschlagen: {e}")

    def release_relative(self, x: float, y: float, window_info: WindowInfo) -> None:
        if not window_info or window_info.width == 0:
            return

        abs_x = int(window_info.x + (window_info.width * x))
        abs_y = int(window_info.y + (window_info.height * y))

        # Up via uinput
        if self._ui:
            try:
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0) # Up
                self._ui.syn()
                logger.debug(f"Maus-Up bei ({abs_x}, {abs_y})")
            except Exception as e:
                logger.error(f"Fehler beim Senden des uinput-Up: {e}")
        else:
            try:
                from pynput.mouse import Button, Controller
                mouse = Controller()
                mouse.release(Button.left)
            except Exception as e:
                logger.error(f"Fallback-Up fehlgeschlagen: {e}")

    def move_relative(self, x: float, y: float, window_info: WindowInfo) -> None:
        abs_x = int(window_info.x + (window_info.width * x))
        abs_y = int(window_info.y + (window_info.height * y))
        try:
            from pynput.mouse import Controller
            mouse = Controller()
            mouse.position = (abs_x, abs_y)
        except:
            pass
