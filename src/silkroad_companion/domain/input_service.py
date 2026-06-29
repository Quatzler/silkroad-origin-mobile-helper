from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from silkroad_companion.domain.models import WindowInfo

class InputService(ABC):
    @abstractmethod
    def bind_key(self, key: str, down_callback: Callable[[], None], up_callback: Optional[Callable[[], None]] = None) -> None:
        """Bindet eine Taste an Callbacks für Drücken und Loslassen."""
        pass

    @abstractmethod
    def unbind_all(self) -> None:
        """Entfernt alle Bindings."""
        pass

    @abstractmethod
    def bind_mouse_click(self, callback: Callable[[], None]) -> None:
        """Bindet den linken Mausklick an einen Callback."""
        pass

class TouchService(ABC):
    @abstractmethod
    def set_screen_size(self, width: int, height: int, offset_x: int = 0, offset_y: int = 0) -> None:
        """Setzt die Bildschirmauflösung und Offsets für die Koordinaten-Skalierung."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Lässt alle Touch-Punkte los."""
        pass

    @abstractmethod
    def click_relative(self, x: float, y: float, window_info: "WindowInfo", slot: int = 0) -> None:
        """Führt einen Klick relativ zum Fenster aus (0.0 - 1.0)."""
        pass

    @abstractmethod
    def press_relative(self, x: float, y: float, window_info: "WindowInfo", slot: int = 0) -> None:
        """Drückt einen Touch-Punkt an einer relativen Position."""
        pass

    @abstractmethod
    def release_relative(self, slot: int = 0) -> None:
        """Lässt einen Touch-Punkt los."""
        pass

    @abstractmethod
    def move_relative(self, x: float, y: float, window_info: "WindowInfo", slot: int = 0) -> None:
        """Bewegt einen Touch-Punkt relativ zum Fenster."""
        pass
