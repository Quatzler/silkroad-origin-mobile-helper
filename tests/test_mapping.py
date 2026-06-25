from unittest.mock import MagicMock
from PySide6.QtCore import QCoreApplication
from silkroad_companion.application.mapping_engine import MappingEngine
from silkroad_companion.application.window_tracker import WindowTracker
from silkroad_companion.domain.config import AppConfig, StateConfig, KeyBind
from silkroad_companion.domain.input_service import InputService, MouseService

def test_mapping_engine_enabling():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window = MagicMock(spec=WindowTracker)
    config = AppConfig(states={
        "game": StateConfig(keybinds={
            "F8": KeyBind(action="test")
        })
    })
    engine = MappingEngine(mock_input, mock_mouse, mock_window, config)

    # Standardmäßig deaktiviert
    assert engine._is_enabled is False

    # Aktivieren
    engine.set_enabled(True)
    assert engine._is_enabled is True
    mock_input.bind_key.assert_called_once()

    # Deaktivieren
    engine.set_enabled(False)
    assert engine._is_enabled is False
    mock_input.unbind_all.assert_called_once()

def test_mapping_engine_state_switch():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window = MagicMock(spec=WindowTracker)
    config = AppConfig(states={
        "game": StateConfig(keybinds={"F8": KeyBind(action="game_act")}),
        "menu": StateConfig(keybinds={"I": KeyBind(action="inv_act")})
    })
    engine = MappingEngine(mock_input, mock_mouse, mock_window, config)
    engine.set_enabled(True)

    mock_input.bind_key.reset_mock()
    engine.set_state("menu")

    # Muss unbind_all aufrufen und dann neue Keys binden
    mock_input.unbind_all.assert_called()
    assert mock_input.bind_key.call_count == 1
    # Prüfen ob "I" gebunden wurde (das erste Argument von bind_key)
    args, _ = mock_input.bind_key.call_args
    assert args[0] == "I"

from silkroad_companion.domain.models import WindowInfo

def test_mapping_engine_test_click():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window_tracker = MagicMock(spec=WindowTracker)
    mock_window_service = MagicMock()
    mock_window_tracker.window_service = mock_window_service

    config = AppConfig(states={
        "game": StateConfig(keybinds={
            "F8": KeyBind(action="test_click")
        })
    })

    # Mock window info
    info = WindowInfo(x=100, y=100, width=800, height=600, focused=True)
    mock_window_service.get_window_info.return_value = info

    engine = MappingEngine(mock_input, mock_mouse, mock_window_tracker, config)
    engine.set_enabled(True)

    # Callback holen
    args, _ = mock_input.bind_key.call_args
    callback = args[1]

    # Ausführen
    callback()
    QCoreApplication.processEvents()

    # Früher mussten wir _execute_action manuell aufrufen,
    # da QTimer im Test ohne Event-Loop nicht feuerte.
    # Jetzt feuert der Fallback in MappingEngine automatisch.

    # Prüfen ob MouseService gerufen wurde
    mock_mouse.click_relative.assert_called_once_with(0.5, 0.5, info)

def test_mapping_engine_back_button_click():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window_tracker = MagicMock(spec=WindowTracker)
    mock_window_service = MagicMock()
    mock_window_tracker.window_service = mock_window_service

    config = AppConfig(states={
        "menu": StateConfig(keybinds={
            "ESC": KeyBind(action="back_button_click")
        })
    })

    # Mock window info
    info = WindowInfo(x=100, y=100, width=1000, height=1000, focused=True)
    mock_window_service.get_window_info.return_value = info

    engine = MappingEngine(mock_input, mock_mouse, mock_window_tracker, config)
    engine.set_state("menu")
    engine.set_enabled(True)

    # Callback holen
    args, _ = mock_input.bind_key.call_args
    callback = args[1]

    # Ausführen
    callback()
    QCoreApplication.processEvents()

    # Prüfen ob MouseService gerufen wurde (0.05, 0.05)
    mock_mouse.click_relative.assert_called_once_with(0.05, 0.05, info)

def test_mapping_engine_custom_coordinates():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window_tracker = MagicMock(spec=WindowTracker)
    mock_window_service = MagicMock()
    mock_window_tracker.window_service = mock_window_service

    config = AppConfig(states={
        "game": StateConfig(keybinds={
            "1": KeyBind(action="any", x=0.1, y=0.2)
        })
    })

    info = WindowInfo(x=0, y=0, width=1000, height=1000, focused=True)
    mock_window_service.get_window_info.return_value = info

    engine = MappingEngine(mock_input, mock_mouse, mock_window_tracker, config)
    engine.set_enabled(True)

    # Callback holen
    args, _ = mock_input.bind_key.call_args
    callback = args[1] # down_callback

    callback()
    QCoreApplication.processEvents()

    # Sollte die Koordinaten aus dem KeyBind nutzen
    mock_mouse.click_relative.assert_called_once_with(0.1, 0.2, info)

def test_mapping_engine_joystick_wasd():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window_tracker = MagicMock(spec=WindowTracker)
    mock_window_service = MagicMock()
    mock_window_tracker.window_service = mock_window_service

    config = AppConfig(states={
        "game": StateConfig(keybinds={
            "W": KeyBind(action="move_forward")
        })
    })

    info = WindowInfo(x=0, y=0, width=1000, height=1000, focused=True)
    mock_window_service.get_window_info.return_value = info

    engine = MappingEngine(mock_input, mock_mouse, mock_window_tracker, config)
    engine.set_enabled(True)

    # Callbacks holen
    # Wir suchen nach "W"
    callbacks = {}
    for call in mock_input.bind_key.call_args_list:
        key, down_cb, up_cb = call[0]
        callbacks[key] = (down_cb, up_cb)

    down_callback, up_callback = callbacks["W"]

    # Down
    down_callback()
    QCoreApplication.processEvents()
    # Joystick Zentrum (0.15, 0.75) -> swipe start
    mock_mouse.press_relative.assert_called_once_with(0.15, 0.75, info)
    # Und dann move zum Ziel (0.15, 0.70)
    mock_mouse.move_relative.assert_called_once_with(0.15, 0.70, info)

    # Up
    up_callback()
    QCoreApplication.processEvents()
    mock_mouse.release_relative.assert_called_once_with(0.15, 0.75, info)

def test_mapping_engine_joystick_diagonal():
    mock_input = MagicMock(spec=InputService)
    mock_mouse = MagicMock(spec=MouseService)
    mock_window_tracker = MagicMock(spec=WindowTracker)
    mock_window_service = MagicMock()
    mock_window_tracker.window_service = mock_window_service

    config = AppConfig(states={
        "game": StateConfig(keybinds={
            "W": KeyBind(action="move_forward"),
            "D": KeyBind(action="move_right")
        })
    })

    info = WindowInfo(x=0, y=0, width=1000, height=1000, focused=True)
    mock_window_service.get_window_info.return_value = info

    engine = MappingEngine(mock_input, mock_mouse, mock_window_tracker, config)
    engine.set_enabled(True)

    callbacks = {}
    for call in mock_input.bind_key.call_args_list:
        key, down_cb, up_cb = call[0]
        callbacks[key] = (down_cb, up_cb)

    # W drücken
    callbacks["W"][0]()
    QCoreApplication.processEvents()
    mock_mouse.press_relative.assert_called_with(0.15, 0.75, info)

    # D dazu drücken
    callbacks["D"][0]()
    QCoreApplication.processEvents()
    # Move zum diagonalen Punkt (0.15 + radius*cos(45), 0.75 - radius*sin(45))
    # Normalisierter Vektor (1, -1) -> (1/sqrt(2), -1/sqrt(2)) approx (0.707, -0.707)
    # Radius = 0.05. Offset x = 0.05 * 0.707 = 0.03535. Offset y = -0.03535.
    # Target approx (0.185, 0.715)

    # Wir prüfen einfach ob move_relative gerufen wurde
    last_move_call = mock_mouse.move_relative.call_args_list[-1]
    tx, ty, _ = last_move_call[0]
    assert 0.18 < tx < 0.19
    assert 0.71 < ty < 0.72

    # W loslassen
    callbacks["W"][1]()
    QCoreApplication.processEvents()
    # Jetzt nur noch D aktiv -> Move to East (0.20, 0.75)
    mock_mouse.move_relative.assert_called_with(0.20, 0.75, info)

    # D loslassen
    callbacks["D"][1]()
    QCoreApplication.processEvents()
    # Release
    mock_mouse.release_relative.assert_called_with(0.15, 0.75, info)
