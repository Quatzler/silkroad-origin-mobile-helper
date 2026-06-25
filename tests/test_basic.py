from unittest.mock import MagicMock

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig
from silkroad_companion.domain.models import AppState
from silkroad_companion.presentation.main_window import MainWindow


def test_app_state_enum():
    assert AppState.GAME.name == "GAME"
    assert AppState.UNKNOWN.name == "UNKNOWN"

def test_main_window_creation(qtbot):
    """Testet ob das Hauptfenster erstellt werden kann."""
    mock_focus = MagicMock(spec=FocusTracker)
    mock_window = MagicMock(spec=WindowTracker)
    config = AppConfig()
    window = MainWindow(mock_focus, mock_window, config)
    qtbot.addWidget(window)
    assert window.windowTitle() == "Silkroad Companion"
