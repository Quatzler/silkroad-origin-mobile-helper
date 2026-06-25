from collections.abc import Callable

from silkroad_companion.domain.focus_service import FocusService


import logging

logger = logging.getLogger(__name__)

class FocusTracker:
    def __init__(self, focus_service: FocusService) -> None:
        self.focus_service = focus_service
        self._observers: list[Callable[[bool, str], None]] = []
        self._last_focus_state = False
        self._last_window_title = ""

    def subscribe(self, callback: Callable[[bool, str], None]) -> None:
        self._observers.append(callback)

    def check_focus(self) -> None:
        is_focused = self.focus_service.is_waydroid_focused()
        window_title = self.focus_service.get_active_window_title() or "Unbekannt"

        # Nur benachrichtigen wenn sich etwas geändert hat
        if is_focused != self._last_focus_state or window_title != self._last_window_title:
            logger.info(f"Fokus-Änderung: {is_focused} ({window_title})")
            self._last_focus_state = is_focused
            self._last_window_title = window_title
            self._notify(is_focused, window_title)

    def _notify(self, is_focused: bool, window_title: str) -> None:
        for observer in self._observers:
            observer(is_focused, window_title)

    @property
    def is_waydroid_focused(self) -> bool:
        return self._last_focus_state

    @property
    def current_window_title(self) -> str:
        return self._last_window_title
