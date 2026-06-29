import logging
from typing import TYPE_CHECKING, Optional, Callable
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.input_service import InputService, TouchService

if TYPE_CHECKING:
    from silkroad_companion.domain.config import KeyBind
    from silkroad_companion.domain.models import WindowInfo

logger = logging.getLogger(__name__)

class MappingEngine:
    def __init__(
        self,
        input_service: InputService,
        touch_service: TouchService,
        window_tracker: WindowTracker,
        config: AppConfig,
    ) -> None:
        self.input_service = input_service
        self.touch_service = touch_service
        self.window_tracker = window_tracker
        self.config = config
        self._is_enabled = False
        self._current_state = "game"  # Standard-State
        self._active_directions: set[str] = set()
        self._picker_mode = False
        self._mouse_pos_provider: Optional[Callable[[], tuple[int, int]]] = None
        
        # Separate Slots für verschiedene Touch-Typen
        # Slot 0: Klicks (Skills, Buttons)
        # Slot 1: Joystick (Bewegung)
        # Slot 2-9: Reserviert für zukünftige Nutzung

    def set_mouse_pos_provider(self, provider: Callable[[], tuple[int, int]]) -> None:
        self._mouse_pos_provider = provider

    def toggle_picker_mode(self) -> None:
        self._picker_mode = not self._picker_mode
        status = "AKTIVIERT" if self._picker_mode else "DEAKTIVIERT"
        print(f"\n--- KOORDINATEN-PICKER {status} ---", flush=True)
        if self._picker_mode:
            print("Klicke mit der Maus im Silkroad-Fenster oder drücke 'F9', um die aktuelle Cursor-Position zu capturen.", flush=True)
        print("-----------------------------------\n", flush=True)

    def capture_cursor_position(self) -> None:
        """Captures the current cursor position and displays relative and uinput coordinates."""
        if not self._mouse_pos_provider:
            print("PICKER: Kein Maus-Positions-Provider verfügbar.", flush=True)
            return

        window_info = self.window_tracker.window_service.get_window_info()
        if not window_info or window_info.width <= 0:
            print("PICKER: Kein Fenster gefunden zum Berechnen der Koordinaten.", flush=True)
            return

        abs_x, abs_y = self._mouse_pos_provider()
        self._print_coordinates(abs_x, abs_y, window_info)

    def handle_mouse_click(self) -> None:
        if not self._picker_mode or not self._mouse_pos_provider:
            return

        window_info = self.window_tracker.window_service.get_window_info()
        if not window_info or window_info.width <= 0:
            print("PICKER: Kein Fenster gefunden zum Berechnen der Koordinaten.", flush=True)
            return

        abs_x, abs_y = self._mouse_pos_provider()
        self._print_coordinates(abs_x, abs_y, window_info)

    def _print_coordinates(self, abs_x: int, abs_y: int, window_info: "WindowInfo") -> None:
        """Prints relative and uinput coordinates for the given absolute position."""
        # Relative Koordinaten berechnen
        rel_x = (abs_x - window_info.x) / window_info.width
        rel_y = (abs_y - window_info.y) / window_info.height

        # Prüfung ob Klick im Fenster liegt
        in_window = 0 <= rel_x <= 1 and 0 <= rel_y <= 1
        status = "IM FENSTER" if in_window else "AUSSERHALB"

        # uinput-Koordinaten berechnen (falls TouchService verfügbar)
        uinput_x, uinput_y = 0, 0
        if hasattr(self.touch_service, '_get_abs_coords'):
            try:
                uinput_x, uinput_y = self.touch_service._get_abs_coords(rel_x, rel_y, window_info)
            except Exception:
                pass

        print("=" * 60, flush=True)
        print("WINDOW DEBUG INFO", flush=True)
        print("=" * 60, flush=True)
        print(f"Cursor Position: ({abs_x}, {abs_y})", flush=True)
        print(f"\nFenster-Geometrie:", flush=True)
        print(f"  Position: ({window_info.x}, {window_info.y})", flush=True)
        print(f"  Größe: {window_info.width}x{window_info.height}", flush=True)
        print(f"  Fokussiert: {window_info.focused}", flush=True)
        print(f"\nRelative Koordinaten: x: {rel_x:.4f}, y: {rel_y:.4f} ({status})", flush=True)
        
        if hasattr(self.touch_service, 'screen_width'):
            print(f"\nTouch-Service Konfiguration:", flush=True)
            print(f"  Screen Size: {self.touch_service.screen_width}x{self.touch_service.screen_height}", flush=True)
            print(f"  Offset: ({self.touch_service.offset_x}, {self.touch_service.offset_y})", flush=True)
        
        if uinput_x > 0 or uinput_y > 0:
            print(f"\nTouch-Koordinaten (uinput 0-32767):", flush=True)
            print(f"  Aktuelle Position -> uinput ({uinput_x}, {uinput_y})", flush=True)
        
        print("=" * 60, flush=True)

        if not in_window:
            print(f"Hinweis: Cursor liegt außerhalb des Fensters!", flush=True)

    def set_enabled(self, enabled: bool) -> None:
        if self._is_enabled == enabled:
            return

        logger.info(f"Mapping Engine enabled set to: {enabled}")
        self._is_enabled = enabled
        if enabled:
            self._apply_mappings()
        else:
            self.input_service.unbind_all()
            self._active_directions.clear()
            self.touch_service.reset()
            logger.info("Mapping Engine deaktiviert.")

    def set_state(self, state_name: str) -> None:
        if self._current_state == state_name:
            return

        logger.info(f"Mapping Engine State Wechsel: {self._current_state} -> {state_name}")
        self._current_state = state_name
        if self._is_enabled:
            # Re-apply mappings for new state
            self.input_service.unbind_all()
            self._apply_mappings()

    def _apply_mappings(self) -> None:
        # Mausklick für Koordinaten-Picker IMMER binden, wenn Engine aktiv ist
        # (auch wenn für den aktuellen State kein Mapping existiert)
        self.input_service.bind_mouse_click(self._create_mouse_callback())

        state_cfg = self.config.states.get(self._current_state)
        if not state_cfg:
            logger.warning(f"Keine Konfiguration für State '{self._current_state}' gefunden.")
            return

        # Wir binden erst alle Keys
        for key, bind in state_cfg.keybinds.items():
            down_cb = self._create_callback(key, bind, is_down=True)
            up_cb = self._create_callback(key, bind, is_down=False)
            self.input_service.bind_key(key, down_cb, up_cb)

        # Und starten den Listener einmalig für alle Keys
        if hasattr(self.input_service, "start_listener"):
            self.input_service.start_listener()

        logger.info(f"Mappings für State '{self._current_state}' aktiviert.")

    def _create_callback(self, key: str, bind: "KeyBind", is_down: bool = True):
        def callback() -> None:
            # Wir nutzen einen Timer, um die Aktion im GUI-Thread auszuführen,
            # da evdev Callbacks in einem eigenen Thread laufen.
            from PySide6.QtCore import QCoreApplication, QTimer
            app = QCoreApplication.instance()
            if app:
                QTimer.singleShot(0, app, lambda: self._execute_action(key, bind, is_down))
            else:
                self._execute_action(key, bind, is_down)
        return callback

    def _create_mouse_callback(self):
        def callback() -> None:
            from PySide6.QtCore import QCoreApplication, QTimer
            app = QCoreApplication.instance()
            if app:
                QTimer.singleShot(0, app, self.handle_mouse_click)
            else:
                self.handle_mouse_click()
        return callback

    def _execute_action(self, key: str, bind: "KeyBind", is_down: bool = True) -> None:
        action = bind.action

        # Wir führen Aktionen standardmäßig beim Drücken aus.
        # Joystick-Aktionen (WASD) brauchen aber auch das Loslassen.
        is_joystick = action.startswith("move_")

        if not is_down and not is_joystick:
            return

        # Hier loggen wir den Hotkey-Druck laut Phase 5 Anforderung
        # Wir nutzen flush=True, damit die Ausgabe sofort in der Konsole erscheint
        suffix = "gedrückt" if is_down else "losgelassen"
        print(f"Hotkey {key} {suffix} -> Action: {action}", flush=True)
        logger.info(f"Hotkey {key} {suffix} -> Action: {action}")

        # Aktuelle Fenster-Info holen
        window_info = self.window_tracker.window_service.get_window_info()
        if not window_info or not window_info.focused:
            logger.warning("Aktion abgebrochen: Fenster nicht fokussiert oder keine Info.")
            return

        # Wenn X und Y in der Config angegeben sind, nutzen wir diese
        if bind.x is not None and bind.y is not None:
            if is_down:
                print(f"Config-Klick bei ({bind.x}, {bind.y})", flush=True)
                self.touch_service.click_relative(bind.x, bind.y, window_info, slot=0)
            return

        # Phase 10: Joystick Simulation (WASD)
        # WICHTIG: Joystick nutzt Slot 1, damit er unabhängig von Klicks (Slot 0) ist
        if is_joystick:
            self._handle_joystick(action, is_down, window_info)
            return

        # Nur bei Tastendruck (is_down=True)
        if not is_down:
            return

        # Phase 6: Test-Klick bei F8 (oder Picker-Modus umschalten)
        if action == "test_click" or action == "toggle_picker":
            self.toggle_picker_mode()

        # Neue Aktion: Cursor-Position capturen
        elif action == "capture_cursor":
            self.capture_cursor_position()

        # Phase 8: Zurück-Button Klick (oben links) im Inventar oder Menüs
        elif action == "back_button_click":
            # Oben links ist oft der Zurück-Button (Android Standard)
            # Sagen wir 5% vom Rand
            rel_x, rel_y = 0.05, 0.05
            print(f"Zurück-Klick bei ({rel_x}, {rel_y}) -> Absolut ({int(window_info.x + window_info.width*rel_x)}, {int(window_info.y + window_info.height*rel_y)})", flush=True)
            self.touch_service.click_relative(rel_x, rel_y, window_info, slot=0)

        # Phase 9: Skill Mapping 1-9
        elif action.startswith("skill_"):
            try:
                skill_num = int(action.split("_")[1])
                # Silkroad Skills 1-9 sind unten in der Mitte/Rechts Leiste.
                # Wir definieren hier beispielhaft Koordinaten (muss später verfeinert werden).
                # Typische Position für Skill 1 (links in der Leiste): 0.6, 0.9
                # Skill 2: 0.65, 0.9 usw.
                base_x = 0.6
                spacing = 0.05
                rel_x = base_x + (skill_num - 1) * spacing
                rel_y = 0.9
                print(f"Skill {skill_num} Klick bei ({rel_x}, {rel_y})", flush=True)
                self.touch_service.click_relative(rel_x, rel_y, window_info, slot=0)
            except (ValueError, IndexError):
                logger.error(f"Ungültige Skill-Aktion: {action}")

        # Phase 9: Attack (Space)
        elif action == "attack":
            # Angriffs-Button ist typischerweise unten rechts
            rel_x, rel_y = 0.95, 0.9
            print(f"Angriff-Klick bei ({rel_x}, {rel_y})", flush=True)
            self.touch_service.click_relative(rel_x, rel_y, window_info, slot=0)

        # Inventar, Map, Char Buttons
        elif action == "inventory":
            rel_x, rel_y = 0.85, 0.05
            self.touch_service.click_relative(rel_x, rel_y, window_info, slot=0)
        elif action == "map":
            rel_x, rel_y = 0.15, 0.225
            self.touch_service.click_relative(rel_x, rel_y, window_info, slot=0)
        elif action == "char":
            rel_x, rel_y = 0.05, 0.05
            self.touch_service.click_relative(rel_x, rel_y, window_info, slot=0)

    def _handle_joystick(self, action: str, is_down: bool, window_info: "WindowInfo") -> None:
        """Simuliert den virtuellen Joystick für Bewegungen.
        
        WICHTIG: Der Joystick nutzt Slot 1, damit er unabhängig von Klicks (Slot 0) ist.
        Dies ermöglicht gleichzeitiges Laufen (WASD) und Kamera-Drehen (Maus).
        """
        state_cfg = self.config.states.get(self._current_state)
        joy_cfg = None
        if state_cfg and state_cfg.joystick:
            joy_cfg = state_cfg.joystick

        # Defaults falls keine Config da ist
        center_x = joy_cfg.center_x if joy_cfg else 0.15
        center_y = joy_cfg.center_y if joy_cfg else 0.75
        radius = joy_cfg.radius if joy_cfg else 0.05

        # Richtung tracken
        direction = action.replace("move_", "")
        if is_down:
            self._active_directions.add(direction)
        else:
            self._active_directions.discard(direction)

        if not self._active_directions:
            # Kein Key mehr gedrückt -> Release
            print("Joystick Stop", flush=True)
            self.touch_service.release_relative(slot=1)
            return

        # Ziel berechnen basierend auf allen aktiven Richtungen
        dx, dy = 0.0, 0.0
        if "forward" in self._active_directions:
            dy -= 1.0
        if "backward" in self._active_directions:
            dy += 1.0
        if "left" in self._active_directions:
            dx -= 1.0
        if "right" in self._active_directions:
            dx += 1.0

        # Normalisieren falls diagonal (damit wir nicht weiter "swipen" als bei axial)
        import math
        mag = math.sqrt(dx*dx + dy*dy)
        if mag > 0:
            dx /= mag
            dy /= mag

        target_x = center_x + dx * radius
        target_y = center_y + dy * radius

        if is_down and len(self._active_directions) == 1:
            # Erster Tastendruck -> Swipe vom Zentrum starten
            print(f"Joystick Start Swipe: ({center_x}, {center_y}) -> ({target_x}, {target_y})", flush=True)
            self.touch_service.press_relative(center_x, center_y, window_info, slot=1)
            import time
            time.sleep(0.02)
            self.touch_service.move_relative(target_x, target_y, window_info, slot=1)
        else:
            # Update Position
            print(f"Joystick Update: ({target_x}, {target_y})", flush=True)
            self.touch_service.move_relative(target_x, target_y, window_info, slot=1)
