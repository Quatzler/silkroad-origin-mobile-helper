from abc import ABC, abstractmethod
from silkroad_companion.domain.models import WindowInfo

class WindowService(ABC):
    @abstractmethod
    def get_window_info(self) -> WindowInfo:
        """Gibt aktuelle Informationen über das Silkroad-Fenster zurück."""
        pass

    @abstractmethod
    def get_cursor_pos(self) -> tuple[int, int]:
        """Gibt die aktuelle globale Cursor-Position zurück."""
        pass
