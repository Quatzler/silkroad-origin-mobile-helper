import pytest
import numpy as np
from unittest.mock import MagicMock
from silkroad_companion.application.vision_engine import VisionEngine
from silkroad_companion.domain.vision_service import VisionService
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.models import WindowInfo

def test_vision_engine_update():
    mock_service = MagicMock(spec=VisionService)
    mock_tracker = MagicMock(spec=WindowTracker)

    # Mock window info
    info = WindowInfo(x=10, y=20, width=100, height=200, focused=True)
    mock_tracker.current_info = info

    # Mock capture
    fake_frame = np.zeros((200, 100, 3), dtype=np.uint8)
    mock_service.capture_window.return_value = fake_frame

    engine = VisionEngine(mock_service, mock_tracker)
    engine.update()

    mock_service.capture_window.assert_called_once_with(info)
    assert engine.last_frame.shape == (200, 100, 3)

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
