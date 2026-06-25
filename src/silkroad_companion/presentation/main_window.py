from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.models import WindowInfo


class MainWindow(QMainWindow):
    def __init__(self, focus_tracker: FocusTracker, window_tracker: WindowTracker, config: AppConfig) -> None:
        super().__init__()
        self.focus_tracker = focus_tracker
        self.window_tracker = window_tracker
        self.config = config
        self.setWindowTitle("Silkroad Companion")
        self.resize(400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Silkroad Companion bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.focus_label = QLabel("Focus: Unbekannt")
        self.focus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.focus_label)

        self.window_label = QLabel("Fenster: -")
        self.window_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.window_label)

        self.geometry_label = QLabel("Geometrie: -")
        self.geometry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.geometry_label)

        self.config_label = QLabel(f"Config: {len(self.config.states)} States geladen")
        self.config_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.config_label)

        # Tracker abonnieren
        self.focus_tracker.subscribe(self.update_focus_status)
        self.window_tracker.subscribe(self.update_window_info)

        # Timer für regelmäßige Prüfung
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._perform_checks)
        self.timer.start(1000)

    def _perform_checks(self) -> None:
        self.focus_tracker.check_focus()
        self.window_tracker.check_window()

    def update_window_info(self, info: WindowInfo) -> None:
        if info.width > 0:
            self.geometry_label.setText(
                f"Geometrie: {info.width}x{info.height} @ ({info.x}, {info.y})"
            )
        else:
            self.geometry_label.setText("Geometrie: Unbekannt")

    def update_focus_status(self, is_focused: bool, window_title: str) -> None:
        status_text = "Waydroid FOKUSSIERT" if is_focused else "Waydroid NICHT fokussiert"
        color = "green" if is_focused else "red"

        self.focus_label.setText(
            f"Focus: <span style='color: {color}; font-weight: bold;'>{status_text}</span>"
        )
        self.window_label.setText(f"Fenster: {window_title}")

        # Konsolen-Ausgabe laut Phase 2 Anforderung
        if is_focused:
            print("Waydroid gefunden")
            print("Waydroid fokussiert")
        else:
            print("Waydroid nicht fokussiert")
