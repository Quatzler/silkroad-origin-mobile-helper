import logging
import numpy as np
from silkroad_companion.domain.vision_service import VisionService
from silkroad_companion.application.window_tracker import WindowTracker

logger = logging.getLogger(__name__)

class VisionEngine:
    def __init__(self, vision_service: VisionService, window_tracker: WindowTracker) -> None:
        self.vision_service = vision_service
        self.window_tracker = window_tracker
        self._last_frame: np.ndarray = np.array([])

    def update(self) -> None:
        window_info = self.window_tracker.current_info
        if not window_info or not window_info.focused:
            return

        frame = self.vision_service.capture_window(window_info)
        if frame.size > 0:
            self._last_frame = frame
            # Hier könnte man erste State-Checks machen
            # logger.debug("Frame erfasst.")

    def detect_state(self, template: np.ndarray) -> bool:
        if self._last_frame.size == 0:
            return False
        return self.vision_service.find_template(self._last_frame, template)

    @property
    def last_frame(self) -> np.ndarray:
        return self._last_frame
