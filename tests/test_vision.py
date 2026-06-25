import pytest
import numpy as np
from unittest.mock import MagicMock
from silkroad_companion.application.vision_engine import VisionEngine
from silkroad_companion.domain.vision_service import VisionService
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.models import WindowInfo, AppState

def test_vision_engine_update():
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)

    # Mock window info
    info = WindowInfo(x=10, y=20, width=100, height=200, focused=True)
    mock_tracker.current_info = info

    # Mock capture
    fake_frame = np.zeros((200, 100, 3), dtype=np.uint8)
    mock_service.capture_window.return_value = fake_frame
    mock_service.find_template.return_value = False # Kein Template gefunden

    engine = VisionEngine(mock_service, mock_tracker)

    # Observer mock
    observer = MagicMock()
    engine.subscribe(observer)

    engine.update()

    mock_service.capture_window.assert_called_once_with(info)
    assert engine.last_frame.shape == (200, 100, 3)
    # Wenn kein Template passt, aber Bild da ist -> Fallback zu GAME
    assert engine.current_state == AppState.GAME
    observer.assert_called_with(AppState.GAME)

def test_vision_engine_state_transitions():
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)
    mock_tracker.current_info = WindowInfo(focused=True, width=100, height=100)

    # Capture Frame
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_service.capture_window.return_value = frame

    engine = VisionEngine(mock_service, mock_tracker)

    # Simuliere gefundenes Menu Template
    menu_template = np.ones((10, 10, 3), dtype=np.uint8)
    engine._templates[AppState.MENU] = [("test_menu.png", menu_template)]

    # find_template soll True geben wenn das menu_template gesucht wird
    def side_effect(img, templ, threshold=0.8):
        return np.array_equal(templ, menu_template)

    mock_service.find_template.side_effect = side_effect

    engine.update()
    assert engine.current_state == AppState.MENU

def test_vision_engine_fallback_to_game():
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)
    mock_tracker.current_info = WindowInfo(focused=True, width=100, height=100)

    # Capture schlägt fehl (size=0)
    mock_service.capture_window.return_value = np.array([])

    engine = VisionEngine(mock_service, mock_tracker)
    assert engine.current_state == AppState.UNKNOWN

    engine.update()
    # Sollte zu GAME wechseln wegen Fallback für fokussierte Fenster
    assert engine.current_state == AppState.GAME

def test_vision_engine_image_smaller_than_template():
    # Testet den Fall, dass das Bild kleiner als das Template ist (OpenCV Assertion Error Fix)
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)
    mock_tracker.current_info = WindowInfo(focused=True, width=50, height=50)

    # Bild ist 50x50
    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    mock_service.capture_window.return_value = frame

    engine = VisionEngine(mock_service, mock_tracker)

    # Template ist 100x100 (größer als Bild)
    large_template = np.zeros((100, 100, 3), dtype=np.uint8)
    engine._templates[AppState.MENU] = [("large.png", large_template)]

    # find_template sollte False zurückgeben (ohne zu crashen)
    mock_service.find_template.return_value = False

    # Update ausführen
    engine.update()

    # Sollte nicht crashen und im Zweifel auf GAME gehen (Fallback)
    assert engine.current_state == AppState.GAME
    mock_service.find_template.assert_called()

def test_vision_engine_no_focus():
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)

    # Not focused
    mock_tracker.current_info = WindowInfo(x=0, y=0, width=100, height=100, focused=False)

    engine = VisionEngine(mock_service, mock_tracker)
    engine.update()

    mock_service.capture_window.assert_not_called()
    assert engine.last_frame.size == 0

def test_vision_engine_detect_state():
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)

    engine = VisionEngine(mock_service, mock_tracker)
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    engine._last_frame = fake_frame

    template = np.zeros((10, 10, 3), dtype=np.uint8)
    mock_service.find_template.return_value = True

    result = engine.detect_state(template)

    mock_service.find_template.assert_called_once_with(fake_frame, template)
    assert result is True
