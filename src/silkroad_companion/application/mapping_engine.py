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

        self._is_enabled = enabled
        if enabled:
            self._apply_mappings()
        else:
            self.input_service.unbind_all()
            logger.info("Mapping Engine deaktiviert.")

    def set_state(self, state_name: str) -> None:
        if self._current_state == state_name:
            return

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
            # da pynput Callbacks in einem eigenen Thread laufen.
            # Das verhindert Blocking und Synchronisationsprobleme.
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._execute_action(key, action))
        return callback

    def _execute_action(self, key: str, action: str) -> None:
        # Hier loggen wir den Hotkey-Druck laut Phase 5 Anforderung
        # Wir nutzen flush=True, damit die Ausgabe sofort in der Konsole erscheint
        print(f"Hotkey {key} gedrückt -> Action: {action}", flush=True)
        logger.info(f"Hotkey {key} gedrückt -> Action: {action}")

        # Phase 6: Test-Klick bei F8
        if action == "test_click":
            # Wir holen uns die aktuelle Info direkt vom Service,
            # um sicherzustellen, dass sie absolut frisch ist.
            window_info = self.window_tracker.window_service.get_window_info()
            if window_info and window_info.focused:
                # Klick in die Mitte des Fensters
                print(f"Relativer Klick bei (0.5, 0.5) -> Absolut ({window_info.x + window_info.width//2}, {window_info.y + window_info.height//2})", flush=True)
                self.mouse_service.click_relative(0.5, 0.5, window_info)
            else:
                logger.warning("Klick abgebrochen: Fenster nicht fokussiert oder keine Info.")
