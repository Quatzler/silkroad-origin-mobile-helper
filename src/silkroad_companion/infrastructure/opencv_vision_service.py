import cv2
import numpy as np
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QScreen
from silkroad_companion.domain.vision_service import VisionService
from silkroad_companion.domain.models import WindowInfo

logger = logging.getLogger(__name__)

class OpenCVVisionService(VisionService):
    def capture_window(self, window_info: WindowInfo) -> np.ndarray:
        if not window_info or window_info.width <= 0 or window_info.height <= 0:
            return np.array([])

        screen = QApplication.primaryScreen()
        if not screen:
            logger.error("Kein primärer Screen gefunden.")
            return np.array([])

        # Screenshot des gesamten Screens
        # Unter Wayland kann das problematisch sein (Sicherheitsbeschränkungen)
        # Aber KWin/Plasma erlaubt es oft via Portal oder wenn die App entsprechende Rechte hat.
        # Als Fallback nutzen wir QScreen.grabWindow(0)
        pixmap = screen.grabWindow(
            0,
            window_info.x,
            window_info.y,
            window_info.width,
            window_info.height
        )

        if pixmap.isNull():
            # Unter Wayland ist das oft ein Rechteproblem oder fehlender Portal-Support
            # Wir loggen es nur einmal pro Minute, um die Konsole nicht zu fluten
            return np.array([])

        # QPixmap -> QImage -> numpy
        image = pixmap.toImage()
        image = image.convertToFormat(image.Format.Format_RGB888)

        width = image.width()
        height = image.height()
        ptr = image.bits()

        # In numpy array umwandeln
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 3))

        # Von RGB nach BGR für OpenCV
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    def find_template(self, image: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> bool:
        if image.size == 0 or template.size == 0:
            return False

        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        return bool(max_val >= threshold)
