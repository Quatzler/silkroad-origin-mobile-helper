from unittest.mock import MagicMock

from silkroad_companion.application.focus_tracker import FocusTracker
from silkroad_companion.domain.focus_service import FocusService


def test_focus_tracker_notifies_on_change():
    mock_service = MagicMock(spec=FocusService)
    mock_service.is_waydroid_focused.return_value = True
    mock_service.get_active_window_title.return_value = "Waydroid"

    tracker = FocusTracker(mock_service)

    callback = MagicMock()
    tracker.subscribe(callback)

    # Erste Prüfung -> Änderung von False/"" zu True/"Waydroid"
    tracker.check_focus()
    callback.assert_called_once_with(True, "Waydroid")

    # Zweite Prüfung -> Keine Änderung
    tracker.check_focus()
    assert callback.call_count == 1

    # Dritte Prüfung -> Titel ändert sich
    mock_service.get_active_window_title.return_value = "Silkroad"
    tracker.check_focus()
    assert callback.call_count == 2
    callback.assert_called_with(True, "Silkroad")

def test_focus_tracker_properties():
    mock_service = MagicMock(spec=FocusService)
    mock_service.is_waydroid_focused.return_value = True
    mock_service.get_active_window_title.return_value = "Test"

    tracker = FocusTracker(mock_service)
    tracker.check_focus()

    assert tracker.is_waydroid_focused is True
    assert tracker.current_window_title == "Test"
