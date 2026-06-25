from PySide6.QtCore import Qt, QTimer, QFileSystemWatcher
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.mapping_engine import MappingEngine
from silkroad_companion.application.vision_engine import VisionEngine
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.models import AppState, WindowInfo
from silkroad_companion.infrastructure.config_loader import ConfigLoader


class MainWindow(QMainWindow):
    def __init__(
        self,
        focus_tracker: FocusTracker,
        window_tracker: WindowTracker,
        vision_engine: VisionEngine,
        config: AppConfig,
        mapping_engine: MappingEngine,
        config_loader: ConfigLoader,
    ) -> None:
        super().__init__()
        self.focus_tracker = focus_tracker
        self.window_tracker = window_tracker
        self.vision_engine = vision_engine
        self.config = config
        self.mapping_engine = mapping_engine
        self.config_loader = config_loader
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

        self.state_label = QLabel("State: UNKNOWN")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.state_label)

        # Tracker abonnieren
        self.focus_tracker.subscribe(self.update_focus_status)
        self.window_tracker.subscribe(self.update_window_info)
        self.vision_engine.subscribe(self.update_game_state)

        # Hot Reload für Konfiguration
        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath("config/settings.yaml")
        self.watcher.fileChanged.connect(self._reload_config)

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
        # Wir überschreiben den Status hier nicht mehr blind,
        # da update_focus_status sich um die Grundzustände kümmert.

    def update_window_info(self, info: WindowInfo) -> None:
        if info.width > 0:
            self.geometry_label.setText(
                f"Geometrie: {info.width}x{info.height} @ ({info.x}, {info.y})"
            )
        else:
            self.geometry_label.setText("Geometrie: Unbekannt")

    def update_game_state(self, state: AppState) -> None:
        self.state_label.setText(f"State: {state.name}")
        # Synchronisiere Mapping Engine mit State
        self.mapping_engine.set_state(state.name.lower())

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

    def _reload_config(self, path: str) -> None:
        print(f"Hot Reload: Konfiguration geändert ({path})", flush=True)
        try:
            new_config = self.config_loader.load()
            self.config = new_config
            self.mapping_engine.config = new_config

            # Falls Engine aktiv ist, Mappings neu anwenden
            if self.mapping_engine._is_enabled:
                self.mapping_engine.input_service.unbind_all()
                self.mapping_engine._apply_mappings()

            self.config_label.setText(f"Config: {len(self.config.states)} States geladen (RELOADED)")
            print("Konfiguration erfolgreich neu geladen.", flush=True)
        except Exception as e:
            print(f"Fehler beim Hot Reload: {e}", flush=True)
            self.config_label.setText(f"Config Error: {e}")
