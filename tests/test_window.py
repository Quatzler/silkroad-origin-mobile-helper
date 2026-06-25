from unittest.mock import Mock
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.models import WindowInfo
from silkroad_companion.domain.window_service import WindowService

def test_window_tracker_notifies_on_change():
    mock_service = Mock(spec=WindowService)
    initial_info = WindowInfo(x=10, y=20, width=100, height=200, focused=True)
    mock_service.get_window_info.return_value = initial_info

    tracker = WindowTracker(mock_service)
    observer = Mock()
    tracker.subscribe(observer)

    # Erste Prüfung
    tracker.check_window()
    observer.assert_called_once_with(initial_info)

    # Keine Änderung -> kein erneuter Aufruf
    observer.reset_mock()
    tracker.check_window()
    observer.assert_not_called()

    # Geometrie ändert sich
    new_info = WindowInfo(x=15, y=20, width=100, height=200, focused=True)
    mock_service.get_window_info.return_value = new_info
    tracker.check_window()
    observer.assert_called_once_with(new_info)

def test_window_tracker_notifies_on_focus_change():
    mock_service = Mock(spec=WindowService)
    info1 = WindowInfo(x=10, y=20, width=100, height=200, focused=True)
    mock_service.get_window_info.return_value = info1

    tracker = WindowTracker(mock_service)
    observer = Mock()
    tracker.subscribe(observer)

    tracker.check_window()
    observer.assert_called_once()

    # Nur Fokus ändert sich
    info2 = WindowInfo(x=10, y=20, width=100, height=200, focused=False)
    mock_service.get_window_info.return_value = info2
    observer.reset_mock()
    tracker.check_window()
    observer.assert_called_once_with(info2)
