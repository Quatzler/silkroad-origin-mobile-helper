from abc import ABC, abstractmethod
from silkroad_companion.domain.models import WindowInfo

class WindowService(ABC):
    @abstractmethod
    def get_window_info(self) -> WindowInfo:
        """Gibt aktuelle Informationen über das Silkroad-Fenster zurück."""
        pass
