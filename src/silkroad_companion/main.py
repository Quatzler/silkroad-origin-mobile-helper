import sys

from PySide6.QtWidgets import QApplication

from PySide6.QtGui import QCursor
from PySide6.QtCore import QTimer
from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.mapping_engine import MappingEngine
from silkroad_companion.application.vision_engine import VisionEngine
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.infrastructure.config_loader import ConfigLoader
from silkroad_companion.infrastructure.keyboard_input_service import EvdevInputService
from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
from silkroad_companion.infrastructure.opencv_vision_service import OpenCVVisionService
from silkroad_companion.presentation.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Silkroad Companion")
    app.setApplicationVersion("0.1.0")

    # Konfiguration laden
    config_loader = ConfigLoader()
    config = config_loader.load()

    # Dependency Injection
    focus_service = KWinFocusService()
    focus_tracker = FocusTracker(focus_service)
    window_tracker = WindowTracker(focus_service)
    input_service = EvdevInputService()
    touch_service = EvdevTouchService()

    # Bildschirmgröße für Touch-Mapping setzen (Gesamter Desktop-Bereich)
    total_rect = None
    for screen in app.screens():
        if total_rect is None:
            total_rect = screen.geometry()
        else:
            total_rect = total_rect.united(screen.geometry())

    if total_rect:
        touch_service.set_screen_size(
            total_rect.width(),
            total_rect.height(),
            total_rect.x(),
            total_rect.y()
        )

    vision_service = OpenCVVisionService()
    vision_engine = VisionEngine(vision_service, window_tracker)
    mapping_engine = MappingEngine(input_service, touch_service, window_tracker, config)

    # Mouse-Position Provider für Koordinaten-Picker setzen
    mapping_engine.set_mouse_pos_provider(lambda: focus_service.get_cursor_pos())

    window = MainWindow(focus_tracker, window_tracker, vision_engine, config, mapping_engine, config_loader)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
