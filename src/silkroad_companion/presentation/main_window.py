from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.mapping_engine import MappingEngine
from silkroad_companion.application.vision_engine import VisionEngine
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.models import WindowInfo


class MainWindow(QMainWindow):
    def __init__(
        self,
        focus_tracker: FocusTracker,
        window_tracker: WindowTracker,
        vision_engine: VisionEngine,
        config: AppConfig,
        mapping_engine: MappingEngine,
    ) -> None:
        super().__init__()
        self.focus_tracker = focus_tracker
        self.window_tracker = window_tracker
        self.vision_engine = vision_engine
        self.config = config
        self.mapping_engine = mapping_engine
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

        self.vision_label = QLabel("Vision: Bereit")
        self.vision_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.vision_label)

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
        self.vision_engine.update()

        # Kleines Feedback in der UI ob Frames kommen
        if self.vision_engine.last_frame.size > 0:
            self.vision_label.setText("Vision: Aktiv (Frame erfasst)")
        elif not self.mapping_engine._is_enabled:
            self.vision_label.setText("Vision: Bereit (Warte auf Fokus)")
        # Wenn wir im Fokus sind, aber kein Frame kommt (Wayland),
        # lassen wir den Text bei "Vision: Aktiv", der in update_focus_status gesetzt wird.

    def update_window_info(self, info: WindowInfo) -> None:
        if info.width > 0:
            self.geometry_label.setText(
                f"Geometrie: {info.width}x{info.height} @ ({info.x}, {info.y})"
            )
        else:
            self.geometry_label.setText("Geometrie: Unbekannt")

    def update_focus_status(self, is_focused: bool, window_title: str) -> None:
        # Mapping Engine aktivieren/deaktivieren basierend auf Fokus
        try:
            self.mapping_engine.set_enabled(is_focused)
        except Exception as e:
            # Fehler loggen, aber GUI nicht abstürzen lassen
            print(f"Warnung: Mapping Engine konnte nicht gesteuert werden: {e}")

        status_text = "Waydroid FOKUSSIERT" if is_focused else "Waydroid NICHT fokussiert"
        color = "green" if is_focused else "red"

        self.focus_label.setText(
            f"Focus: <span style='color: {color}; font-weight: bold;'>{status_text}</span>"
        )
        self.window_label.setText(f"Fenster: {window_title}")

        if is_focused:
            self.vision_label.setText("Vision: Aktiv")
            print("Waydroid gefunden", flush=True)
            print("Waydroid fokussiert", flush=True)
        else:
            self.vision_label.setText("Vision: Bereit (Warte auf Fokus)")
            print("Waydroid nicht fokussiert", flush=True)
