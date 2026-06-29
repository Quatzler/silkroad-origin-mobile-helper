import logging
import evdev
from evdev import ecodes, UInput, AbsInfo
from silkroad_companion.domain.input_service import TouchService
from silkroad_companion.domain.models import WindowInfo
import time

logger = logging.getLogger(__name__)

class EvdevTouchService(TouchService):
    def __init__(self) -> None:
        self.max_x = 32767
        self.max_y = 32767
        self.screen_width = 1920 # Default
        self.screen_height = 1080 # Default
        self.offset_x = 0
        self.offset_y = 0
        self._ui = self._create_uinput_device()
        self._active_slots: dict[int, int] = {} # slot -> tracking_id
        self._next_tracking_id = 1

    def set_screen_size(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0) -> None:
        logger.info(f"Touch-Service Screen Size gesetzt: {width}x{height} bei ({offset_x}, {offset_y})")
        self.screen_width = width
        self.screen_height = height
        self.offset_x = offset_x
        self.offset_y = offset_y

    def reset(self) -> None:
        if not self._ui:
            return
        logger.info("Touch-Service Reset: Alle Slots loslassen")
        try:
            # Alle aktiven Slots nacheinander schließen
            for slot in list(self._active_slots.keys()):
                self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, slot)
                self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TRACKING_ID, -1)

            self._ui.write(ecodes.EV_KEY, ecodes.BTN_TOUCH, 0)
            self._ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_FINGER, 0)
            self._ui.syn()
            self._active_slots.clear()
        except Exception as e:
            logger.error(f"Fehler bei Touch-Reset: {e}")

    def _create_uinput_device(self) -> UInput | None:
        try:
            # Wir erstellen einen virtuellen Multitouch-Screen
            capabilities = {
                ecodes.EV_KEY: [ecodes.BTN_TOUCH, ecodes.BTN_TOOL_FINGER],
                ecodes.EV_ABS: [
                    (ecodes.ABS_X, AbsInfo(0, 0, self.max_x, 0, 0, 0)),
                    (ecodes.ABS_Y, AbsInfo(0, 0, self.max_y, 0, 0, 0)),
                    (ecodes.ABS_MT_SLOT, AbsInfo(0, 0, 9, 0, 0, 0)),
                    (ecodes.ABS_MT_TRACKING_ID, AbsInfo(0, 0, 65535, 0, 0, 0)),
                    (ecodes.ABS_MT_POSITION_X, AbsInfo(0, 0, self.max_x, 0, 0, 0)),
                    (ecodes.ABS_MT_POSITION_Y, AbsInfo(0, 0, self.max_y, 0, 0, 0)),
                    (ecodes.ABS_MT_TOUCH_MAJOR, AbsInfo(0, 0, 255, 0, 0, 0)),
                    (ecodes.ABS_MT_PRESSURE, AbsInfo(0, 0, 255, 0, 0, 0)),
                ],
            }
            # INPUT_PROP_DIRECT sagt dem System, dass es ein Touchscreen ist (kein Touchpad)
            ui = UInput(
                capabilities,
                name="Silkroad-Companion-Virtual-Touch",
                version=0x1,
                input_props=[ecodes.INPUT_PROP_DIRECT]
            )
            logger.info("Virtueller Touchscreen via uinput erstellt.")
            return ui
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des uinput Touch-Geräts: {e}")
            return None

    def _get_abs_coords(self, x: float, y: float, window_info: WindowInfo) -> tuple[int, int]:
        # Absolute Pixel-Position auf dem Desktop berechnen
        abs_px_x = window_info.x + (window_info.width * x)
        abs_px_y = window_info.y + (window_info.height * y)

        logger.info(f"Touch-Mapping: Rel ({x}, {y}) -> Abs Pixel ({int(abs_px_x)}, {int(abs_px_y)})")

        # Skalierung auf uinput-Bereich (0..max_x) basierend auf Screen-Größe
        # Wir müssen den Desktop-Offset abziehen, um bei der Gesamt-Desktop-Breite/Höhe
        # die korrekte relative Position zu finden.
        tx = int(((abs_px_x - self.offset_x) / self.screen_width) * self.max_x)
        ty = int(((abs_px_y - self.offset_y) / self.screen_height) * self.max_y)

        logger.info(f"Touch-Mapping: uinput coords ({tx}, {ty})")

        # Begrenzung auf gültigen Bereich
        tx = max(0, min(self.max_x, tx))
        ty = max(0, min(self.max_y, ty))

        return tx, ty

    def click_relative(self, x: float, y: float, window_info: WindowInfo, slot: int = 0) -> None:
        self.press_relative(x, y, window_info, slot)
        time.sleep(0.05)
        self.release_relative(slot)

    def press_relative(self, x: float, y: float, window_info: WindowInfo, slot: int = 0) -> None:
        if not self._ui or not window_info or window_info.width == 0:
            return

        tx, ty = self._get_abs_coords(x, y, window_info)

        tid = self._next_tracking_id
        self._next_tracking_id = (self._next_tracking_id + 1) % 65536
        self._active_slots[slot] = tid

        try:
            if len(self._active_slots) == 1:
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_TOUCH, 1)
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_FINGER, 1)

            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, slot)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TRACKING_ID, tid)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_POSITION_X, tx)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_POSITION_Y, ty)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TOUCH_MAJOR, 5)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_PRESSURE, 50)

            # Für Single-Touch Kompatibilität (ABS_X/Y)
            if slot == 0:
                self._ui.write(ecodes.EV_ABS, ecodes.ABS_X, tx)
                self._ui.write(ecodes.EV_ABS, ecodes.ABS_Y, ty)

            self._ui.syn()
            logger.debug(f"Touch-Press Slot {slot} bei ({tx}, {ty}), TID {tid}")

        except Exception as e:
            logger.error(f"Fehler bei Touch-Press: {e}")

    def release_relative(self, slot: int = 0) -> None:
        if not self._ui or slot not in self._active_slots:
            return

        try:
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, slot)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TRACKING_ID, -1)

            # Wenn keine Slots mehr aktiv sind, BTN_TOUCH und BTN_TOOL_FINGER auf 0
            del self._active_slots[slot]
            if not self._active_slots:
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_TOUCH, 0)
                self._ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_FINGER, 0)

            self._ui.syn()
            logger.debug(f"Touch-Release Slot {slot}")
        except Exception as e:
            logger.error(f"Fehler bei Touch-Release: {e}")

    def move_relative(self, x: float, y: float, window_info: WindowInfo, slot: int = 0) -> None:
        if not self._ui or not window_info or window_info.width == 0:
            return

        tx, ty = self._get_abs_coords(x, y, window_info)

        try:
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_SLOT, slot)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_POSITION_X, tx)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_POSITION_Y, ty)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_TOUCH_MAJOR, 5)
            self._ui.write(ecodes.EV_ABS, ecodes.ABS_MT_PRESSURE, 50)

            if slot == 0:
                self._ui.write(ecodes.EV_ABS, ecodes.ABS_X, tx)
                self._ui.write(ecodes.EV_ABS, ecodes.ABS_Y, ty)

            self._ui.syn()
            logger.debug(f"Touch-Move Slot {slot} zu ({tx}, {ty})")
        except Exception as e:
            logger.error(f"Fehler bei Touch-Move: {e}")
