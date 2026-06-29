import pytest
from unittest.mock import MagicMock, patch
from silkroad_companion.infrastructure.kwin_focus_service import KWinFocusService

@patch("silkroad_companion.infrastructure.kwin_focus_service.QDBusConnection.sessionBus")
@patch("silkroad_companion.infrastructure.kwin_focus_service.QDBusInterface")
@patch("silkroad_companion.infrastructure.kwin_focus_service.subprocess.Popen")
def test_parsing_robustness(mock_popen, mock_dbus_iface, mock_bus):
    # Mock KWin script setup
    mock_popen.return_value.stdout = None

    service = KWinFocusService()

    # Test Normal
    service._parse_line("SRO_GEOMETRY:100,200,300,400")
    assert service._current_geometry == (100, 200, 300, 400)

    # Test mit "js:" Präfix (wie vom User gemeldet)
    service._parse_line("js: SRO_GEOMETRY:862,412,408,332")
    assert service._current_geometry == (862, 412, 408, 332)

    # Test mit Floats
    service._parse_line("js: SRO_GEOMETRY:623.0248615676642,210.08155942973497,1280,720")
    assert service._current_geometry == (623, 210, 1280, 720)

    # Test Focus Class mit Präfix
    service._parse_line("js: SRO_FOCUS_CLASS:waydroid.com.silkroad.mb")
    assert service._current_focus_class == "waydroid.com.silkroad.mb"
    assert service.is_waydroid_focused() is True

    # Test Focus Title mit Präfix
    service._parse_line("js: SRO_FOCUS_TITLE:Silkroad Origin Mobile")
    assert service._current_window_title == "Silkroad Origin Mobile"

    # Test Cursor
    service._parse_line("js: SRO_CURSOR:500,600")
    assert service.get_cursor_pos() == (500, 600)

    # Test Cursor mit Floats
    service._parse_line("SRO_CURSOR:500.5,600.9")
    assert service.get_cursor_pos() == (500, 600)
