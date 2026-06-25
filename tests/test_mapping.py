from unittest.mock import MagicMock
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
        "inventory": StateConfig(keybinds={"I": KeyBind(action="inv_act")})
    })
    engine = MappingEngine(mock_input, mock_mouse, mock_window, config)
    engine.set_enabled(True)

    mock_input.bind_key.reset_mock()
    engine.set_state("inventory")

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
        "inventory": StateConfig(keybinds={
            "ESC": KeyBind(action="back_button_click")
        })
    })

    # Mock window info
    info = WindowInfo(x=100, y=100, width=1000, height=1000, focused=True)
    mock_window_service.get_window_info.return_value = info

    engine = MappingEngine(mock_input, mock_mouse, mock_window_tracker, config)
    engine.set_state("inventory")
    engine.set_enabled(True)

    # Callback holen
    args, _ = mock_input.bind_key.call_args
    callback = args[1]

    # Ausführen
    callback()

    # Prüfen ob MouseService gerufen wurde (0.05, 0.05)
    mock_mouse.click_relative.assert_called_once_with(0.05, 0.05, info)
