import sys

from PySide6.QtWidgets import QApplication

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.mapping_engine import MappingEngine
from silkroad_companion.application.vision_engine import VisionEngine
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.infrastructure.config_loader import ConfigLoader
from silkroad_companion.infrastructure.keyboard_input_service import KeyboardInputService
from silkroad_companion.infrastructure.mouse_input_service import EvdevMouseService
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
    input_service = KeyboardInputService()
    mouse_service = EvdevMouseService()
    vision_service = OpenCVVisionService()
    vision_engine = VisionEngine(vision_service, window_tracker)
    mapping_engine = MappingEngine(input_service, mouse_service, window_tracker, config)

    window = MainWindow(focus_tracker, window_tracker, vision_engine, config, mapping_engine)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
