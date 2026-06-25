import logging
import os
import cv2
import numpy as np
from silkroad_companion.domain.vision_service import VisionService
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.models import AppState

logger = logging.getLogger(__name__)

class VisionEngine:
    def __init__(self, vision_service: VisionService, window_tracker: WindowTracker) -> None:
        self.vision_service = vision_service
        self.window_tracker = window_tracker
        self._last_frame: np.ndarray = np.array([])
        self._current_state: AppState = AppState.UNKNOWN
        self._state_observers: list[callable] = []
        self._templates: dict[AppState, list[np.ndarray]] = {
            AppState.LOGIN: [],
            AppState.GAME: [],
            AppState.INVENTORY: [],
        }
        self._load_templates()

    def _load_templates(self) -> None:
        template_base_path = "templates"
        if not os.path.exists(template_base_path):
            logger.warning(f"Template-Verzeichnis {template_base_path} nicht gefunden.")
            return

        for state in self._templates.keys():
            state_path = os.path.join(template_base_path, state.name.lower())
            if os.path.exists(state_path):
                for file in os.listdir(state_path):
                    if file.endswith((".png", ".jpg", ".jpeg")):
                        path = os.path.join(state_path, file)
                        template = cv2.imread(path)
                        if template is not None:
                            self._templates[state].append(template)
                            logger.info(f"Template geladen für {state.name}: {file}")

    def subscribe(self, callback: callable) -> None:
        self._state_observers.append(callback)

    def update(self) -> None:
        window_info = self.window_tracker.current_info
        if not window_info or not window_info.focused:
            if self._current_state != AppState.UNKNOWN:
                self._current_state = AppState.UNKNOWN
                self._notify_state_change()
            return

        frame = self.vision_service.capture_window(window_info)
        if frame.size > 0:
            self._last_frame = frame
            self._analyze_state()
        else:
            # Fallback: Wenn wir fokussiert sind, aber kein Bild kriegen (Wayland!),
            # gehen wir zumindest von GAME aus, damit Mappings funktionieren.
            if self._current_state == AppState.UNKNOWN:
                self._set_state(AppState.GAME)

    def _analyze_state(self) -> None:
        # Template-Matching für jeden registrierten State
        # Wir priorisieren INVENTORY und LOGIN vor GAME

        # 1. Spezifische Zustände prüfen
        for state in [AppState.INVENTORY, AppState.LOGIN]:
            for template in self._templates[state]:
                if self.vision_service.find_template(self._last_frame, template):
                    if self._current_state != state:
                        logger.info(f"Template-Match: {state.name} erkannt")
                    self._set_state(state)
                    return

        # 2. Prüfen ob wir im GAME sind (via Minimap o.ä.)
        for template in self._templates[AppState.GAME]:
            if self.vision_service.find_template(self._last_frame, template):
                if self._current_state != AppState.GAME:
                    logger.info("Template-Match: GAME erkannt (Minimap)")
                self._set_state(AppState.GAME)
                return

        # 3. Wenn wir ein Bild haben, aber nichts erkannt wurde,
        # gehen wir von GAME aus (da wir fokussiert sind).
        # Dies ist der Standardzustand für Silkroad.
        if self._current_state != AppState.GAME:
            logger.info("Kein Template-Match, Fallback auf GAME")
        self._set_state(AppState.GAME)

    def _set_state(self, new_state: AppState) -> None:
        if new_state != self._current_state:
            self._current_state = new_state
            logger.info(f"State gewechselt: {new_state.name}")
            self._notify_state_change()

    def _notify_state_change(self) -> None:
        for observer in self._state_observers:
            observer(self._current_state)

    def detect_state(self, template: np.ndarray) -> bool:
        if self._last_frame.size == 0:
            return False
        return self.vision_service.find_template(self._last_frame, template)

    @property
    def last_frame(self) -> np.ndarray:
        return self._last_frame

    @property
    def current_state(self) -> AppState:
        return self._current_state
