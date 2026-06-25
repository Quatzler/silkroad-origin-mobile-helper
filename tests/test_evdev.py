import pytest
from unittest.mock import MagicMock, patch
from silkroad_companion.infrastructure.keyboard_input_service import KeyboardInputService

def test_keyboard_service_build_map():
    service = KeyboardInputService()
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

    service = KeyboardInputService()
    devices = service._find_keyboard_devices()

    assert len(devices) == 1
    assert devices[0].name == "Test Keyboard"

@patch("evdev.UInput")
def test_mouse_service_uinput(mock_uinput):
    from silkroad_companion.infrastructure.mouse_input_service import EvdevMouseService
    service = EvdevMouseService()
    assert service._ui is not None
    mock_uinput.assert_called_once()
