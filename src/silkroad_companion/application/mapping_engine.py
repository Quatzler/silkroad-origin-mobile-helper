import logging
from typing import TYPE_CHECKING
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.input_service import InputService, MouseService

if TYPE_CHECKING:
    from silkroad_companion.domain.config import KeyBind

logger = logging.getLogger(__name__)

class MappingEngine:
    def __init__(
        self,
        input_service: InputService,
        mouse_service: MouseService,
        window_tracker: WindowTracker,
        config: AppConfig,
    ) -> None:
        self.input_service = input_service
        self.mouse_service = mouse_service
        self.window_tracker = window_tracker
        self.config = config
        self._is_enabled = False
        self._current_state = "game"  # Standard-State
        self._active_directions: set[str] = set()

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
            # Wir übergeben QCoreApplication.instance() als Context, um sicherzustellen,
            # dass der Callback im Haupt-Thread (GUI-Thread) ausgeführt wird.
            from PySide6.QtCore import QCoreApplication, QTimer
            app = QCoreApplication.instance()
            if app:
                QTimer.singleShot(0, app, lambda: self._execute_action(key, bind, is_down))
            else:
                # Fallback für Tests ohne laufende App
                self._execute_action(key, bind, is_down)
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
                self.mouse_service.click_relative(bind.x, bind.y, window_info)
            return

        # Phase 10: Joystick Simulation (WASD)
        if is_joystick:
            self._handle_joystick(action, is_down, window_info)
            return

        # Nur bei Tastendruck (is_down=True)
        if not is_down:
            return

        # Phase 6: Test-Klick bei F8
        if action == "test_click":
            # Klick in die Mitte des Fensters
            print(f"Relativer Klick bei (0.5, 0.5) -> Absolut ({window_info.x + window_info.width//2}, {window_info.y + window_info.height//2})", flush=True)
            self.mouse_service.click_relative(0.5, 0.5, window_info)

        # Phase 8: Zurück-Button Klick (oben links) im Inventar oder Menüs
        elif action == "back_button_click":
            # Oben links ist oft der Zurück-Button (Android Standard)
            # Sagen wir 5% vom Rand
            rel_x, rel_y = 0.05, 0.05
            print(f"Zurück-Klick bei ({rel_x}, {rel_y}) -> Absolut ({int(window_info.x + window_info.width*rel_x)}, {int(window_info.y + window_info.height*rel_y)})", flush=True)
            self.mouse_service.click_relative(rel_x, rel_y, window_info)

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
                self.mouse_service.click_relative(rel_x, rel_y, window_info)
            except (ValueError, IndexError):
                logger.error(f"Ungültige Skill-Aktion: {action}")

    def _handle_joystick(self, action: str, is_down: bool, window_info: "WindowInfo") -> None:
        """Simuliert den virtuellen Joystick für Bewegungen."""
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
            self.mouse_service.release_relative(center_x, center_y, window_info)
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
            self.mouse_service.press_relative(center_x, center_y, window_info)
            import time
            time.sleep(0.02)
            self.mouse_service.move_relative(target_x, target_y, window_info)
        else:
            # Update Position
            print(f"Joystick Update: ({target_x}, {target_y})", flush=True)
            self.mouse_service.move_relative(target_x, target_y, window_info)
