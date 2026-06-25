import sys

from PySide6.QtWidgets import QApplication

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.infrastructure.config_loader import ConfigLoader
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService
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

    window = MainWindow(focus_tracker, window_tracker, config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
