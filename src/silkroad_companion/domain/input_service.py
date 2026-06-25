from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from silkroad_companion.domain.models import WindowInfo

class InputService(ABC):
    @abstractmethod
    def bind_key(self, key: str, callback: Callable[[], None]) -> None:
        """Bindet eine Taste an einen Callback."""
        pass

    @abstractmethod
    def unbind_all(self) -> None:
        """Entfernt alle Bindings."""
        pass

class MouseService(ABC):
    @abstractmethod
    def click_relative(self, x: float, y: float, window_info: "WindowInfo") -> None:
        """Führt einen Klick relativ zum Fenster aus (0.0 - 1.0)."""
        pass

    @abstractmethod
    def move_relative(self, x: float, y: float, window_info: "WindowInfo") -> None:
        """Bewegt die Maus relativ zum Fenster."""
        pass
