import logging
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.input_service import InputService, MouseService

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

    def set_enabled(self, enabled: bool) -> None:
        if self._is_enabled == enabled:
            return

        logger.info(f"Mapping Engine enabled set to: {enabled}")
        self._is_enabled = enabled
        if enabled:
            self._apply_mappings()
        else:
            self.input_service.unbind_all()
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
            action_name = bind.action
            self.input_service.bind_key(key, self._create_callback(key, action_name))

        # Und starten den Listener einmalig für alle Keys
        if hasattr(self.input_service, "start_listener"):
            self.input_service.start_listener()

        logger.info(f"Mappings für State '{self._current_state}' aktiviert.")

    def _create_callback(self, key: str, action: str):
        def callback() -> None:
            # Wir nutzen einen Timer, um die Aktion im GUI-Thread auszuführen,
            # da evdev Callbacks in einem eigenen Thread laufen.
            # Wir übergeben QCoreApplication.instance() als Context, um sicherzustellen,
            # dass der Callback im Haupt-Thread (GUI-Thread) ausgeführt wird.
            from PySide6.QtCore import QCoreApplication, QTimer
            app = QCoreApplication.instance()
            if app:
                QTimer.singleShot(0, app, lambda: self._execute_action(key, action))
            else:
                # Fallback für Tests ohne laufende App
                self._execute_action(key, action)
        return callback

    def _execute_action(self, key: str, action: str) -> None:
        # Hier loggen wir den Hotkey-Druck laut Phase 5 Anforderung
        # Wir nutzen flush=True, damit die Ausgabe sofort in der Konsole erscheint
        print(f"Hotkey {key} gedrückt -> Action: {action}", flush=True)
        logger.info(f"Hotkey {key} gedrückt -> Action: {action}")

        # Aktuelle Fenster-Info holen
        window_info = self.window_tracker.window_service.get_window_info()
        if not window_info or not window_info.focused:
            logger.warning("Aktion abgebrochen: Fenster nicht fokussiert oder keine Info.")
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
