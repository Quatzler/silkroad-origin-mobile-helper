from collections.abc import Callable
from silkroad_companion.domain.window_service import WindowService
from silkroad_companion.domain.models import WindowInfo

class WindowTracker:
    def __init__(self, window_service: WindowService) -> None:
        self.window_service = window_service
        self._observers: list[Callable[[WindowInfo], None]] = []
        self._last_info: WindowInfo | None = None

    def subscribe(self, callback: Callable[[WindowInfo], None]) -> None:
        self._observers.append(callback)

    def check_window(self) -> None:
        current_info = self.window_service.get_window_info()

        # Nur benachrichtigen wenn sich etwas Wesentliches geändert hat
        if self._last_info is None or \
           current_info.x != self._last_info.x or \
           current_info.y != self._last_info.y or \
           current_info.width != self._last_info.width or \
           current_info.height != self._last_info.height or \
           current_info.focused != self._last_info.focused:

            self._last_info = current_info
            self._notify(current_info)

    def _notify(self, info: WindowInfo) -> None:
        for observer in self._observers:
            observer(info)

    @property
    def current_info(self) -> WindowInfo | None:
        return self._last_info
