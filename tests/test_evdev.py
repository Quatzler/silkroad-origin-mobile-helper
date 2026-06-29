import pytest
from unittest.mock import MagicMock, patch
from silkroad_companion.infrastructure.keyboard_input_service import EvdevInputService

def test_keyboard_service_build_map():
    service = EvdevInputService()
    # Prüfen ob gängige Tasten im Mapping sind
    assert "f8" in service._key_names_to_codes
    assert "a" in service._key_names_to_codes
    assert "esc" in service._key_names_to_codes

@patch("evdev.list_devices")
@patch("evdev.InputDevice")
def test_find_keyboard_devices(mock_input_device, mock_list_devices):
    mock_list_devices.return_value = ["/dev/input/event0"]

    mock_dev = MagicMock()
    mock_dev.name = "Test Keyboard"
    mock_dev.path = "/dev/input/event0"
    # EV_KEY: { KEY_A: ... }
    from evdev import ecodes
    mock_dev.capabilities.return_value = {
        ecodes.EV_KEY: [ecodes.KEY_A]
    }
    mock_input_device.return_value = mock_dev

    service = EvdevInputService()
    devices = service._find_input_devices()

    assert len(devices) == 1
    assert devices[0].name == "Test Keyboard"

@patch("evdev.UInput")
def test_touch_service_uinput(mock_uinput):
    from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
    service = EvdevTouchService()
    assert service._ui is not None
    mock_uinput.assert_called_once()

@patch("evdev.UInput")
def test_touch_scaling(mock_uinput):
    from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
    from silkroad_companion.domain.models import WindowInfo
    service = EvdevTouchService()
    service.set_screen_size(1920, 1080, 0, 0)

    window_info = WindowInfo(x=100, y=100, width=800, height=600, focused=True)
    tx, ty = service._get_abs_coords(0.5, 0.5, window_info)

    assert tx == int((500 / 1920) * 32767)
    assert ty == int((400 / 1080) * 32767)

@patch("evdev.UInput")
def test_touch_scaling_offset(mock_uinput):
    from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
    from silkroad_companion.domain.models import WindowInfo
    service = EvdevTouchService()
    # Desktop von -1920 bis 1920 (Breite 3840), Offset -1920
    service.set_screen_size(3840, 1080, -1920, 0)

    # Fenster auf dem rechten Monitor bei (100, 100)
    window_info = WindowInfo(x=100, y=100, width=800, height=600, focused=True)
    tx, ty = service._get_abs_coords(0.5, 0.5, window_info)

    # x = 100 + 400 = 500. Relativ zum linken Rand (-1920) ist das 500 - (-1920) = 2420.
    assert tx == int((2420 / 3840) * 32767)

@patch("evdev.UInput")
def test_touch_reset(mock_uinput):
    from silkroad_companion.infrastructure.touch_input_service import EvdevTouchService
    service = EvdevTouchService()
    service._ui = MagicMock()
    service._active_slots[1] = 123
    service.reset()
    assert service._ui.write.called
    assert 1 not in service._active_slots
